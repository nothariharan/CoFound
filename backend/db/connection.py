"""Motor client helpers for MongoDB Atlas."""

from __future__ import annotations

import os

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> AsyncIOMotorDatabase:
    """Connect to MongoDB Atlas and return the database handle."""

    global _client, _db
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured")
    db_name = os.getenv("MONGODB_DB", "cofounder").strip() or "cofounder"
    # Long-running FastAPI service: reuse one client, pre-warm a small pool for agent polling.
    _client = AsyncIOMotorClient(
        uri,
        tlsCAFile=certifi.where(),
        minPoolSize=5,
        maxPoolSize=50,
        maxIdleTimeMS=300_000,
        connectTimeoutMS=10_000,
        serverSelectionTimeoutMS=5_000,
        socketTimeoutMS=30_000,
    )
    _db = _client[db_name]
    await _client.admin.command("ping")
    return _db


async def close_db() -> None:
    """Close the Motor client."""

    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the active database handle."""

    if _db is None:
        raise RuntimeError("Database is not connected")
    return _db


def is_connected() -> bool:
    """Whether a database connection is active."""

    return _db is not None
