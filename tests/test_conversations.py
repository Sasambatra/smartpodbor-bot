from datetime import UTC, datetime

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.methods import AnswerCallbackQuery, EditMessageReplyMarkup, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from smartphone_bot.catalog import load_catalog
from smartphone_bot.demo import EXAMPLE_ANSWERS
from smartphone_bot.handlers import Survey, create_router
from smartphone_bot.questions import QUESTIONS
from smartphone_bot.storage import SQLiteStorage

BOT_USER = User(
    id=123456789, is_bot=True, first_name="СмартПодбор", username="smartpodbor_test_bot"
)


class FakeSession(BaseSession):
    """Runs real dispatcher handlers without any requests to Telegram."""

    def __init__(self):
        super().__init__()
        self.calls = []
        self.sent = []

    async def close(self):
        pass

    async def make_request(self, bot, method, timeout=None):  # noqa: ASYNC109 - BaseSession API
        self.calls.append(method)
        if isinstance(method, SendMessage):
            message = Message(
                message_id=1000 + len(self.sent),
                date=datetime.now(UTC),
                chat=Chat(id=method.chat_id, type="private"),
                from_user=BOT_USER,
                text=method.text,
                reply_markup=method.reply_markup,
            ).as_(bot)
            self.sent.append(message)
            return message
        if isinstance(method, (AnswerCallbackQuery, EditMessageReplyMarkup)):
            return True
        raise AssertionError(f"Unexpected Telegram method: {type(method).__name__}")

    async def stream_content(self, *args, **kwargs):
        yield b""


class Conversation:
    def __init__(self, path):
        self.session = FakeSession()
        self.bot = Bot(
            token="123456789:" + "A" * 35,
            session=self.session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.storage = SQLiteStorage(path)
        self.dispatcher = Dispatcher(storage=self.storage, events_isolation=SimpleEventIsolation())
        self.dispatcher.include_router(create_router(load_catalog()))
        self.sequence = 0

    def state(self, user_id=42):
        return self.dispatcher.fsm.get_context(bot=self.bot, chat_id=user_id, user_id=user_id)

    async def message(self, text=None, user_id=42, chat_type="private"):
        self.sequence += 1
        message = Message(
            message_id=self.sequence,
            date=datetime.now(UTC),
            chat=Chat(id=user_id, type=chat_type),
            from_user=User(id=user_id, is_bot=False, first_name="Тест"),
            text=text,
        )
        await self.dispatcher.feed_update(
            self.bot, Update(update_id=self.sequence, message=message)
        )

    async def callback(self, payload, user_id=42):
        self.sequence += 1
        message = next(
            message for message in reversed(self.session.sent) if message.chat.id == user_id
        )
        callback = CallbackQuery(
            id=str(self.sequence),
            chat_instance="test",
            from_user=User(id=user_id, is_bot=False, first_name="Тест"),
            message=message,
            data=payload,
        )
        await self.dispatcher.feed_update(
            self.bot, Update(update_id=self.sequence, callback_query=callback)
        )

    async def answer(self, value, user_id=42):
        data = await self.state(user_id).get_data()
        payload = f"a:{data['nonce']}:{data['index']}:{value}"
        await self.callback(payload, user_id)
        return payload

    async def close(self):
        await self.storage.close()
        await self.bot.session.close()


@pytest_asyncio.fixture
async def chat(tmp_path):
    conversation = Conversation(tmp_path / "bot.sqlite3")
    yield conversation
    await conversation.close()


async def finish_survey(chat, answers=None):
    await chat.message("/choose")
    for question in QUESTIONS:
        await chat.answer((answers or EXAMPLE_ANSWERS)[question.key])


async def test_complete_survey_sends_three_different_phones_with_nine_shop_links(chat):
    await chat.message("/start")
    assert "СмартПодбор" in chat.session.sent[-1].text
    await finish_survey(chat)
    assert await chat.state().get_state() == Survey.results.state
    cards = [message for message in chat.session.sent if "Ориентир:" in message.text]
    assert len(cards) == 3
    assert "POCO X7 Pro" in cards[0].text
    links = [
        button.url for card in cards for row in card.reply_markup.inline_keyboard for button in row
    ]
    assert len(links) == 9
    assert all(url.startswith("https://") for url in links)
    assert "Цены ориентировочные" in "\n".join(message.text for message in chat.session.sent)


async def test_stale_or_double_click_does_not_advance_survey_twice(chat):
    await chat.message("/choose")
    old_payload = await chat.answer("40000")
    await chat.callback(old_payload)
    assert (await chat.state().get_data())["index"] == 1
    assert "устарела" in chat.session.calls[-1].text


async def test_parallel_double_click_is_serialized(chat):
    import asyncio

    await chat.message("/choose")
    data = await chat.state().get_data()
    payload = f"a:{data['nonce']}:0:40000"
    await asyncio.gather(chat.callback(payload), chat.callback(payload))
    assert (await chat.state().get_data())["index"] == 1


async def test_custom_budget_back_and_cancel(chat):
    await chat.message("/choose")
    await chat.message("35 тыс.")
    assert (await chat.state().get_data())["answers"]["budget"] == "35000"
    await chat.answer("android")
    await chat.message("/back")
    data = await chat.state().get_data()
    assert data["index"] == 1
    assert "os" not in data["answers"]
    await chat.message("/cancel")
    assert await chat.state().get_state() is None
    assert await chat.state().get_data() == {}


async def test_media_invalid_budget_and_unknown_command_do_not_corrupt_state(chat):
    await chat.message("/choose")
    for text in (None, "-5000", "no", "/something"):
        await chat.message(text)
        assert (await chat.state().get_data())["index"] == 0
    await chat.message("/help")
    assert (await chat.state().get_data())["index"] == 0


async def test_users_are_isolated_and_group_messages_are_ignored(chat):
    await chat.message("/choose", user_id=42)
    await chat.message("/choose", user_id=84)
    await chat.answer("25000", user_id=42)
    assert (await chat.state(42).get_data())["index"] == 1
    assert (await chat.state(84).get_data())["index"] == 0
    count = len(chat.session.sent)
    await chat.message("/choose", user_id=-100, chat_type="supergroup")
    assert len(chat.session.sent) == count


async def test_resume_after_restart(tmp_path):
    path = tmp_path / "bot.sqlite3"
    first = Conversation(path)
    try:
        await first.message("/choose")
        await first.answer("40000")
        await first.answer("android")
    finally:
        await first.close()
    second = Conversation(path)
    try:
        await second.message("/start")
        assert "Вопрос 3 из 8" in second.session.sent[-1].text
        assert (await second.state().get_data())["answers"] == {"budget": "40000", "os": "android"}
    finally:
        await second.close()


@pytest.mark.parametrize("changes", [{"budget": "5000"}, {"os": "ios", "budget": "200000"}])
async def test_no_results_is_explained_without_overriding_answers(chat, changes):
    answers = {**EXAMPLE_ANSWERS, **changes}
    await finish_survey(chat, answers)
    assert "Точного совпадения" in chat.session.sent[-1].text
    assert not any("Ориентир:" in message.text for message in chat.session.sent)
    assert (await chat.state().get_data())["answers"] == answers


async def test_results_can_be_repeated_and_edited(chat):
    await finish_survey(chat)
    count = len(chat.session.sent)
    await chat.message("/results")
    assert len(chat.session.sent) == count + 5
    await chat.message("/back")
    assert await chat.state().get_state() == Survey.answering.state
    assert (await chat.state().get_data())["index"] == 7
    await chat.answer("samsung")
    assert await chat.state().get_state() == Survey.results.state
