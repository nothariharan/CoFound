"""motor helpers for atlas connection"""

from __future__ import annotations

import os

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> AsyncIOMotorDatabase:
    """connect to atlas and return the db handle"""

    global _client, _db
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured")
    db_name = os.getenv("MONGODB_DB", "cofounder").strip() or "cofounder"
    # One async client serves the single low-concurrency Render instance.
    # A small, idle-pruned pool avoids reserving memory on the 512 MB plan.
    _client = AsyncIOMotorClient(
        uri,
        tlsCAFile=certifi.where(),
        minPoolSize=0,
        maxPoolSize=5,
        maxIdleTimeMS=45_000,
        connectTimeoutMS=8_000,
        serverSelectionTimeoutMS=8_000,
        socketTimeoutMS=25_000,
    )
    _db = _client[db_name]
    await _client.admin.command("ping")
    return _db


async def close_db() -> None:
    """close the motor client"""

    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    """return the active database handle"""

    if _db is None:
        raise RuntimeError("Database is not connected")
    return _db


def is_connected() -> bool:
    """whether a database connection is active"""

    return _db is not None
