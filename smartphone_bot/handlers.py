"""Adapted from aiogram's MIT-licensed finite_state_machine.py example.

See third_party/aiogram/LICENSE and THIRD_PARTY_NOTICES.md.
"""

import logging
import secrets

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from smartphone_bot.catalog import Catalog
from smartphone_bot.presentation import BUYING_TIPS, recommendation_text, summary_text
from smartphone_bot.questions import QUESTIONS, answer_label, parse_budget, valid_answer
from smartphone_bot.recommendations import (
    Preferences,
    marketplace_links,
    no_results_explanation,
    recommend,
)

logger = logging.getLogger(__name__)


class Survey(StatesGroup):
    answering = State()
    results = State()


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Подобрать смартфон", callback_data="flow:start")],
        ]
    )


def question_keyboard(index: int, nonce: str) -> InlineKeyboardMarkup:
    question = QUESTIONS[index]
    rows = [
        [InlineKeyboardButton(text=option.label, callback_data=f"a:{nonce}:{index}:{option.value}")]
        for option in question.options
    ]
    navigation = []
    if index:
        navigation.append(
            InlineKeyboardButton(text="← Назад", callback_data=f"n:{nonce}:{index}:back")
        )
    navigation.append(
        InlineKeyboardButton(text="Отмена", callback_data=f"n:{nonce}:{index}:cancel")
    )
    rows.append(navigation)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def remove_keyboard(message: Message) -> None:
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        # The message may have been deleted or its keyboard already removed.
        pass


async def show_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    index = data["index"]
    question = QUESTIONS[index]
    progress = "●" * index + "○" * (len(QUESTIONS) - index)
    await message.answer(
        f"<b>Вопрос {index + 1} из {len(QUESTIONS)}</b>  {progress}\n\n"
        f"<b>{question.title}</b>\n{question.hint}",
        reply_markup=question_keyboard(index, data["nonce"]),
    )


async def begin_survey(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Survey.answering)
    await state.set_data({"index": 0, "answers": {}, "nonce": secrets.token_hex(4)})
    await show_question(message, state)


async def go_back(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if "index" not in data:
        await message.answer(
            "Активного опроса нет. Начните подбор кнопкой ниже.", reply_markup=menu_keyboard()
        )
        return
    index = max(0, data["index"] - 1)
    # Later answers must be collected again after editing an earlier answer.
    answers = {question.key: data["answers"][question.key] for question in QUESTIONS[:index]}
    await state.set_data({"index": index, "answers": answers, "nonce": secrets.token_hex(4)})
    await state.set_state(Survey.answering)
    await show_question(message, state)


async def show_results(message: Message, state: FSMContext, catalog: Catalog) -> None:
    data = await state.get_data()
    if await state.get_state() != Survey.results.state:
        await message.answer(
            "Сначала завершите опрос. Продолжить: /start.", reply_markup=menu_keyboard()
        )
        return
    answers = data["answers"]
    preferences = Preferences.from_answers(answers)
    recommendations = recommend(catalog.phones, preferences)
    await message.answer(summary_text(answers, catalog))
    if not recommendations:
        await message.answer(
            "<b>Точного совпадения в каталоге нет.</b>\n\n"
            + no_results_explanation(catalog.phones, preferences)
            + "\n\nБюджет и обязательные условия не меняю автоматически. "
            "Нажмите /back для изменения ответов или /choose для нового подбора.",
            reply_markup=menu_keyboard(),
        )
        return
    for rank, item in enumerate(recommendations, 1):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"🔎 {name}", url=url)]
                for name, url in marketplace_links(item.phone).items()
            ]
        )
        await message.answer(recommendation_text(item, rank), reply_markup=keyboard)
    await message.answer(BUYING_TIPS, reply_markup=menu_keyboard())


async def accept_answer(message: Message, state: FSMContext, value: str, catalog: Catalog) -> None:
    data = await state.get_data()
    index = data["index"]
    question = QUESTIONS[index]
    answers = {**data["answers"], question.key: value}
    await state.set_data({"index": index + 1, "answers": answers, "nonce": secrets.token_hex(4)})
    if index + 1 == len(QUESTIONS):
        await state.set_state(Survey.results)
        await show_results(message, state, catalog)
    else:
        await show_question(message, state)


def create_router(catalog: Catalog, ttl_hours: int = 24) -> Router:
    router = Router(name="smartpodbor")
    # Personal answers stay in private chats; each user has an independent FSM key.
    router.message.filter(F.chat.type == ChatType.PRIVATE)
    router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        if await state.get_state() == Survey.answering.state:
            await message.answer("Продолжим сохранённый опрос. Начать заново: /choose.")
            await show_question(message, state)
            return
        await message.answer(
            "<b>📱 СмартПодбор</b>\n\n"
            "Помогу выбрать смартфон под ваши задачи и бюджет. "
            "Ответьте на 8 коротких вопросов — получите до трёх моделей, "
            "объяснение выбора и ссылки на российские маркетплейсы.\n\n"
            "Цены в каталоге ориентировочные; актуальную стоимость увидите у продавца. "
            f"Ответы хранятся локально до {ttl_hours} ч. после последнего изменения. "
            "Удалить их можно командой /cancel. Подробнее: /privacy.",
            reply_markup=menu_keyboard(),
        )

    @router.message(Command("choose"))
    async def choose(message: Message, state: FSMContext) -> None:
        await begin_survey(message, state)

    @router.message(Command("back"))
    async def back(message: Message, state: FSMContext) -> None:
        await go_back(message, state)

    @router.message(Command("cancel"))
    async def cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            "Опрос остановлен. Сохранённые ответы удалены.", reply_markup=menu_keyboard()
        )

    @router.message(Command("results"))
    async def results(message: Message, state: FSMContext) -> None:
        await show_results(message, state, catalog)

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "<b>Как пользоваться</b>\n"
            "/start — приветствие или продолжение опроса\n"
            "/choose — начать новый подбор\n"
            "/back — вернуться к предыдущему вопросу\n"
            "/results — повторить готовую подборку\n"
            "/cancel — остановить опрос и удалить ответы\n"
            "/privacy — хранение данных\n\n"
            "Отвечайте кнопками под вопросом. На вопрос о бюджете можно написать сумму, "
            "например 35000 или 35 тыс. Бот работает в личном чате. "
            "Для подбора не нужны номер телефона, имя или адрес.",
        )

    @router.message(Command("privacy"))
    async def privacy(message: Message) -> None:
        await message.answer(
            "<b>Данные опроса</b>\n"
            "Локально у владельца бота сохраняются Telegram ID, ответы и текущий шаг. "
            "Ответы не отправляются внешним AI-сервисам или магазинам. "
            f"Сессия истекает через {ttl_hours} ч. после последнего изменения; "
            "истёкшие записи удаляются при следующем обращении к базе. "
            "Команда /cancel сразу удаляет запись с ответами из базы бота. "
            "Сообщения в истории Telegram остаются, пока вы сами их не удалите.\n\n"
            "При переходе в магазин в ссылке передаются модель и объём памяти; "
            "дальше действуют правила соответствующей площадки.",
        )

    @router.callback_query(F.data == "flow:start")
    async def start_button(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        if isinstance(callback.message, Message):
            await remove_keyboard(callback.message)
            await begin_survey(callback.message, state)

    @router.callback_query(F.data.startswith("a:") | F.data.startswith("n:"))
    async def survey_button(callback: CallbackQuery, state: FSMContext) -> None:
        if not isinstance(callback.message, Message):
            await callback.answer()
            return
        data = await state.get_data()
        parts = (callback.data or "").split(":")
        if (
            len(parts) != 4
            or await state.get_state() != Survey.answering.state
            or parts[1] != data.get("nonce")
            or parts[2] != str(data.get("index"))
        ):
            await callback.answer("Эта кнопка устарела. Текущий вопрос ниже или /start.")
            return
        kind, _, _, value = parts
        if kind == "n":
            if value not in {"back", "cancel"}:
                await callback.answer("Неизвестная кнопка.")
                return
            await callback.answer()
            await remove_keyboard(callback.message)
            if value == "back":
                await go_back(callback.message, state)
            else:
                await cancel(callback.message, state)
            return
        question = QUESTIONS[data["index"]]
        if not valid_answer(question, value):
            await callback.answer("Выберите один из предложенных вариантов.")
            return
        await callback.answer(answer_label(question, value))
        await remove_keyboard(callback.message)
        await accept_answer(callback.message, state, value, catalog)

    @router.message(Survey.answering)
    async def typed_answer(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        question = QUESTIONS[data["index"]]
        if message.text and not message.text.startswith("/"):
            if question.key == "budget":
                budget = parse_budget(message.text)
                if budget is not None:
                    await accept_answer(message, state, str(budget), catalog)
                    return
            else:
                option = next(
                    (
                        option
                        for option in question.options
                        if option.label.casefold() == message.text.strip().casefold()
                    ),
                    None,
                )
                if option:
                    await accept_answer(message, state, option.value, catalog)
                    return
        await message.answer(
            "Введите бюджет от 5 000 до 500 000 ₽, например 35000 или 35 тыс."
            if question.key == "budget"
            else "Выберите ответ кнопкой под вопросом. Назад: /back.",
            reply_markup=question_keyboard(data["index"], data["nonce"]),
        )

    @router.callback_query()
    async def old_button(callback: CallbackQuery) -> None:
        await callback.answer("Кнопка устарела. Откройте /start для продолжения.")

    @router.message()
    async def unknown_message(message: Message) -> None:
        await message.answer(
            "Начать подбор: /choose. Готовая подборка: /results. Помощь: /help.",
            reply_markup=menu_keyboard(),
        )

    @router.errors()
    async def on_error(event: ErrorEvent) -> bool:
        # Do not log exception text: HTTP exceptions can contain the bot token.
        logger.error("Update failed (%s)", type(event.exception).__name__)
        message = event.update.message
        if event.update.callback_query:
            candidate = event.update.callback_query.message
            message = candidate if isinstance(candidate, Message) else None
        if message and message.chat.type == ChatType.PRIVATE:
            try:
                await message.answer(
                    "Не получилось обработать ответ. Продолжить: /start. Готовая подборка: /results."
                )
            except Exception:
                logger.error("Could not send recovery message")
        return True

    return router
