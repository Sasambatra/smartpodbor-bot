import sqlite3

import pytest
from aiogram.fsm.storage.base import StorageKey

from smartphone_bot.handlers import Survey
from smartphone_bot.storage import SQLiteStorage


@pytest.mark.asyncio
async def test_sessions_survive_restart_are_isolated_and_can_be_deleted(tmp_path):
    path = tmp_path / "sessions.sqlite3"
    first = StorageKey(bot_id=1, chat_id=100, user_id=100)
    second = StorageKey(bot_id=1, chat_id=200, user_id=200)
    other_bot = StorageKey(bot_id=2, chat_id=100, user_id=100)
    storage = SQLiteStorage(path)
    try:
        await storage.set_state(first, Survey.answering)
        await storage.set_data(first, {"index": 2, "answers": {"budget": "35000"}})
        assert await storage.get_data(second) == {}
        assert await storage.get_state(other_bot) is None
    finally:
        await storage.close()
    restarted = SQLiteStorage(path)
    try:
        assert await restarted.get_state(first) == Survey.answering.state
        assert (await restarted.get_data(first))["answers"]["budget"] == "35000"
        await restarted.set_state(first, None)
        await restarted.set_data(first, {})
        assert await restarted.get_state(first) is None
        assert await restarted.get_data(first) == {}
        async with restarted._connection.execute("SELECT COUNT(*) FROM sessions") as cursor:
            assert (await cursor.fetchone())[0] == 0
    finally:
        await restarted.close()


async def test_expired_rows_are_purged_even_if_user_never_returns(tmp_path, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("smartphone_bot.storage.time.time", lambda: now[0])
    storage = SQLiteStorage(tmp_path / "sessions.sqlite3", ttl_seconds=10)
    first = StorageKey(bot_id=1, chat_id=100, user_id=100)
    second = StorageKey(bot_id=1, chat_id=200, user_id=200)
    try:
        await storage.set_state(first, Survey.answering)
        await storage.set_data(first, {"budget": "35000"})
        now[0] += 11
        assert await storage.get_state(second) is None
        async with storage._connection.execute("SELECT COUNT(*) FROM sessions") as cursor:
            assert (await cursor.fetchone())[0] == 0
        assert await storage.get_data(first) == {}
    finally:
        await storage.close()


async def test_failed_write_rolls_back_cleanup_and_preserves_active_session(tmp_path, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("smartphone_bot.storage.time.time", lambda: now[0])
    storage = SQLiteStorage(tmp_path / "sessions.sqlite3", ttl_seconds=10)
    expired = StorageKey(bot_id=1, chat_id=100, user_id=100)
    active = StorageKey(bot_id=1, chat_id=200, user_id=200)
    try:
        await storage.set_state(expired, Survey.answering)
        now[0] = 1005
        await storage.set_state(active, Survey.answering)
        await storage.set_data(active, {"budget": "35000"})
        await storage._connection.execute(
            "CREATE TRIGGER reject_state BEFORE UPDATE ON sessions "
            "WHEN NEW.state = 'forbidden' BEGIN SELECT RAISE(ABORT, 'rejected'); END"
        )
        await storage._connection.commit()
        now[0] = 1011
        with pytest.raises(sqlite3.IntegrityError):
            await storage.set_state(active, "forbidden")
        async with storage._connection.execute("SELECT COUNT(*) FROM sessions") as cursor:
            # Expiration cleanup is part of the same transaction and was rolled back.
            assert (await cursor.fetchone())[0] == 2
        assert await storage.get_state(active) == Survey.answering.state
        assert await storage.get_data(active) == {"budget": "35000"}
        await storage.set_state(active, Survey.results)
        assert await storage.get_state(active) == Survey.results.state
    finally:
        await storage.close()


async def test_corrupt_database_can_be_replaced_after_failed_initialization(tmp_path):
    path = tmp_path / "sessions.sqlite3"
    path.write_text("not a SQLite database", encoding="utf-8")
    storage = SQLiteStorage(path)
    key = StorageKey(bot_id=1, chat_id=100, user_id=100)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            await storage.get_state(key)
        path.unlink()
        assert await storage.get_state(key) is None
        await storage.set_data(key, {"budget": "25000"})
        assert await storage.get_data(key) == {"budget": "25000"}
    finally:
        await storage.close()
