"""low level mongodb operations routed through the mongodb mcp server"""

from __future__ import annotations

import json
import os
from typing import Any

from db import collections as col
from mdb_mcp.client import call_mcp_tool


def database_name() -> str:
    return os.getenv("MONGODB_DB", "cofounder").strip() or "cofounder"


def _db_args(collection: str, **extra: Any) -> dict[str, Any]:
    payload = {"database": database_name(), "collection": collection}
    payload.update(extra)
    return payload


def _documents_from_result(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        return [doc for doc in result if isinstance(doc, dict)]
    if isinstance(result, dict):
        for key in ("documents", "results", "data", "cursor", "firstBatch"):
            value = result.get(key)
            if isinstance(value, list):
                return [doc for doc in value if isinstance(doc, dict)]
        if "_id" in result or "idea_id" in result or "task_id" in result:
            return [result]
    if isinstance(result, str):
        if "Found 0 documents" in result:
            return []
        try:
            return _documents_from_result(json.loads(result))
        except json.JSONDecodeError:
            start = result.find("[")
            end = result.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return _documents_from_result(json.loads(result[start : end + 1]))
                except json.JSONDecodeError:
                    pass
            start = result.find("{")
            end = result.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return _documents_from_result(json.loads(result[start : end + 1]))
                except json.JSONDecodeError:
                    pass
            return []
    return []


async def mcp_find(
    collection: str,
    *,
    filter: dict[str, Any] | None = None,
    projection: dict[str, Any] | None = None,
    sort: dict[str, Any] | list[Any] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    args = _db_args(collection)
    if filter is not None:
        args["filter"] = filter
    if projection is not None:
        args["projection"] = projection
    if sort is not None:
        args["sort"] = sort
    if limit is not None:
        args["limit"] = limit
    result = await call_mcp_tool("find", args)
    return _documents_from_result(result)


async def mcp_find_one(
    collection: str,
    *,
    filter: dict[str, Any],
    projection: dict[str, Any] | None = None,
    sort: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any] | None:
    docs = await mcp_find(collection, filter=filter, projection=projection, sort=sort, limit=1)
    return docs[0] if docs else None


async def mcp_aggregate(collection: str, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = await call_mcp_tool("aggregate", _db_args(collection, pipeline=pipeline))
    return _documents_from_result(result)


async def mcp_insert_many(collection: str, documents: list[dict[str, Any]]) -> None:
    if documents:
        await call_mcp_tool("insert-many", _db_args(collection, documents=documents))


async def mcp_insert_one(collection: str, document: dict[str, Any]) -> None:
    await mcp_insert_many(collection, [document])


async def mcp_update_many(
    collection: str,
    *,
    filter: dict[str, Any],
    update: dict[str, Any],
    upsert: bool = False,
) -> None:
    args = _db_args(collection, filter=filter, update=update)
    if upsert:
        args["upsert"] = True
    await call_mcp_tool("update-many", args)


async def mcp_replace_workspace(document: dict[str, Any]) -> None:
    await mcp_update_many(
        col.STARTUP_GRAPHS,
        filter={"idea_id": document["idea_id"]},
        update={"$set": document},
        upsert=True,
    )
