import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from aiogram.utils.token import TokenValidationError, validate_token
from dotenv import load_dotenv


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    database_path: Path
    ttl_hours: int
    log_level: str

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(Path.cwd() / ".env", override=False)
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise ConfigError(
                "Добавьте BOT_TOKEN в файл .env. Получить токен: https://t.me/BotFather. "
                "Демо без токена: python -m smartphone_bot --demo"
            )
        try:
            validate_token(token)
        except TokenValidationError:
            raise ConfigError(
                "BOT_TOKEN имеет неверный формат. Проверьте токен из BotFather."
            ) from None
        try:
            ttl = int(os.getenv("SESSION_TTL_HOURS", "24"))
        except ValueError:
            raise ConfigError("SESSION_TTL_HOURS должно быть целым числом от 1 до 720.") from None
        if not 1 <= ttl <= 720:
            raise ConfigError("SESSION_TTL_HOURS должно быть целым числом от 1 до 720.")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigError("LOG_LEVEL: используйте DEBUG, INFO, WARNING, ERROR или CRITICAL.")
        path = os.getenv("DATABASE_PATH", "data/smartpodbor.sqlite3").strip()
        if not path:
            raise ConfigError("DATABASE_PATH не должен быть пустым.")
        return cls(token, Path(path).expanduser(), ttl, log_level)


class RedactingFormatter(logging.Formatter):
    def __init__(self, token: str) -> None:
        super().__init__("%(asctime)s %(levelname)s %(name)s: %(message)s")
        self.token = token

    def format(self, record: logging.LogRecord) -> str:
        return super().format(record).replace(self.token, "[BOT_TOKEN]")


def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter(settings.token))
    logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)
