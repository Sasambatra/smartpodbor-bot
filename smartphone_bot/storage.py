"""SQLite FSM storage for a single polling process, with expiring sessions."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import aiosqlite
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, DefaultKeyBuilder, StateType, StorageKey


class SQLiteStorage(BaseStorage):
    def __init__(self, path: Path, ttl_seconds: int = 86400) -> None:
        self.path = path
        self.ttl_seconds = ttl_seconds
        self._connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()
        self._key_builder = DefaultKeyBuilder(with_bot_id=True, with_destiny=True)

    async def _connect(self) -> aiosqlite.Connection:
        if self._connection is None:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            connection = await aiosqlite.connect(self.path)
            try:
                await connection.execute("PRAGMA journal_mode=WAL")
                await connection.execute(
                    "CREATE TABLE IF NOT EXISTS sessions ("
                    "key TEXT PRIMARY KEY, state TEXT, data TEXT NOT NULL DEFAULT '{}', updated REAL NOT NULL)"
                )
                await connection.execute(
                    "CREATE INDEX IF NOT EXISTS sessions_updated ON sessions(updated)"
                )
                await connection.commit()
            except BaseException:
                await connection.close()
                raise
            self._connection = connection
        return self._connection

    async def _read(self, key: StorageKey) -> tuple[str | None, dict[str, Any]]:
        async with self._lock:
            connection = await self._connect()
            # Purge all expired rows, including users who never return.
            await connection.execute(
                "DELETE FROM sessions WHERE updated < ?", (time.time() - self.ttl_seconds,)
            )
            async with connection.execute(
                "SELECT state, data FROM sessions WHERE key = ?", (self._key_builder.build(key),)
            ) as cursor:
                row = await cursor.fetchone()
            await connection.commit()
            return (row[0], json.loads(row[1])) if row else (None, {})

    async def _write(self, key: StorageKey, column: str, value: Any) -> None:
        if column not in {"state", "data"}:
            raise ValueError("Invalid session column")
        async with self._lock:
            connection = await self._connect()
            try:
                await connection.execute(
                    "DELETE FROM sessions WHERE updated < ?", (time.time() - self.ttl_seconds,)
                )
                await connection.execute(
                    f"INSERT INTO sessions(key, {column}, updated) VALUES (?, ?, ?) "
                    f"ON CONFLICT(key) DO UPDATE SET {column}=excluded.{column}, updated=excluded.updated",
                    (self._key_builder.build(key), value, time.time()),
                )
                await connection.execute(
                    "DELETE FROM sessions WHERE state IS NULL AND data = '{}' "
                )
                await connection.commit()
            except BaseException:
                await connection.rollback()
                raise

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await self._write(key, "state", state.state if isinstance(state, State) else state)

    async def get_state(self, key: StorageKey) -> str | None:
        return (await self._read(key))[0]

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        await self._write(key, "data", json.dumps(data, ensure_ascii=False))

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        return (await self._read(key))[1]

    async def close(self) -> None:
        async with self._lock:
            if self._connection is not None:
                await self._connection.close()
                self._connection = None
