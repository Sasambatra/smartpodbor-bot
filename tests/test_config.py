import logging

import pytest

from smartphone_bot.config import ConfigError, RedactingFormatter, Settings


def test_missing_token_has_setup_instructions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ConfigError, match="BotFather"):
        Settings.load()


def test_invalid_token_is_not_echoed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BOT_TOKEN", "sensitive-invalid-token")
    with pytest.raises(ConfigError) as error:
        Settings.load()
    assert "sensitive-invalid-token" not in str(error.value)


def test_logging_redacts_token():
    token = "123456789:" + "A" * 35
    record = logging.LogRecord(
        "test",
        logging.ERROR,
        __file__,
        1,
        "Failed URL %s",
        (f"https://api.telegram.org/bot{token}/getMe",),
        None,
    )
    result = RedactingFormatter(token).format(record)
    assert token not in result
    assert "[BOT_TOKEN]" in result


def test_settings_repr_does_not_expose_credentials(tmp_path):
    secret = "123456789:" + "B" * 35
    settings = Settings(secret, tmp_path / "bot.sqlite3", 24, "INFO")
    assert secret not in repr(settings)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("SESSION_TTL_HOURS", "0"),
        ("SESSION_TTL_HOURS", "721"),
        ("SESSION_TTL_HOURS", "one"),
        ("LOG_LEVEL", "verbose"),
        ("DATABASE_PATH", " "),
    ],
)
def test_invalid_configuration_is_actionable(tmp_path, monkeypatch, name, value):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BOT_TOKEN", "123456789:" + "B" * 35)
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError, match=name):
        Settings.load()


def test_environment_overrides_local_env_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "BOT_TOKEN=123456789:" + "A" * 35 + "\nSESSION_TTL_HOURS=12\n", encoding="utf-8"
    )
    monkeypatch.delenv("SESSION_TTL_HOURS", raising=False)
    monkeypatch.setenv("BOT_TOKEN", "123456789:" + "B" * 35)
    settings = Settings.load()
    assert settings.token.endswith("B" * 35)
    assert settings.ttl_hours == 12
