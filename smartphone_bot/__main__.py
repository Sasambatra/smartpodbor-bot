import argparse
import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, LinkPreviewOptions

from smartphone_bot.catalog import Catalog, CatalogError, load_catalog
from smartphone_bot.config import ConfigError, Settings, configure_logging
from smartphone_bot.handlers import create_router
from smartphone_bot.storage import SQLiteStorage


async def run_bot(settings: Settings, catalog: Catalog) -> None:
    storage = SQLiteStorage(settings.database_path, settings.ttl_hours * 3600)
    dispatcher = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())
    dispatcher.include_router(create_router(catalog, settings.ttl_hours))
    bot = Bot(
        token=settings.token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview=LinkPreviewOptions(is_disabled=True),
        ),
    )
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Начать или продолжить опрос"),
                BotCommand(command="choose", description="Новый подбор смартфона"),
                BotCommand(command="back", description="Предыдущий вопрос"),
                BotCommand(command="results", description="Показать готовую подборку"),
                BotCommand(command="cancel", description="Остановить опрос и удалить ответы"),
                BotCommand(command="help", description="Как пользоваться"),
                BotCommand(command="privacy", description="Хранение данных"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )
        await bot.delete_webhook(drop_pending_updates=False)
        logging.getLogger(__name__).info(
            "СмартПодбор запущен; %s конфигураций", len(catalog.phones)
        )
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        await storage.close()
        await bot.session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="СмартПодбор — подбор смартфонов в Telegram")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Пройти опрос в терминале без токена")
    mode.add_argument("--check", action="store_true", help="Проверить каталог без Telegram")
    parser.add_argument("--example", action="store_true", help="Готовый пример для режима --demo")
    parser.add_argument("--catalog", type=Path, help="Путь к своему JSON-каталогу смартфонов")
    args = parser.parse_args()
    if args.example and not args.demo:
        parser.error("--example используется вместе с --demo")
    try:
        catalog = load_catalog(args.catalog)
    except CatalogError as error:
        parser.exit(2, f"Каталог: {error}\n")
    if args.check:
        print(
            f"Каталог OK: {len(catalog.phones)} конфигурации, {len({phone.name for phone in catalog.phones})} моделей."
        )
        print(
            f"Характеристики сверены: {catalog.specs_checked_on:%d.%m.%Y}. Цены — ручные ориентиры."
        )
        return
    if args.demo:
        from smartphone_bot.demo import run_demo

        try:
            run_demo(catalog, args.example)
        except (EOFError, KeyboardInterrupt):
            print("\nДемо завершено.")
        return
    try:
        settings = Settings.load()
        configure_logging(settings)
        asyncio.run(run_bot(settings, catalog))
    except ConfigError as error:
        parser.exit(2, f"Настройка: {error}\n")
    except TelegramUnauthorizedError:
        parser.exit(2, "Telegram отклонил токен. Проверьте BOT_TOKEN в .env.\n")
    except KeyboardInterrupt:
        pass
    except Exception as error:
        # Never include a token-bearing request URL in the startup error.
        parser.exit(
            1,
            f"Не удалось запустить бота ({type(error).__name__}). Проверьте сеть, .env и доступ к базе.\n",
        )


if __name__ == "__main__":
    main()
