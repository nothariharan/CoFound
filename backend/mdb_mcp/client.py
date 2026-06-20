"""persistent mongodb mcp client session for runtime agent persistence"""

from __future__ import annotations

import json
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mdb_mcp.mongodb_mcp import get_mcp_connection_string

logger = logging.getLogger(__name__)

_manager: McpSessionManager | None = None


class McpSessionManager:
    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._tool_names: dict[str, str] = {}
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready and self._session is not None

    async def start(self) -> None:
        connection_string = get_mcp_connection_string()
        if not connection_string:
            raise RuntimeError("MDB_MCP_CONNECTION_STRING is not configured")

        command, args = _server_command()
        env = os.environ.copy()
        env["MDB_MCP_CONNECTION_STRING"] = connection_string

        server_params = StdioServerParameters(command=command, args=args, env=env)
        read, write = await self._stack.enter_async_context(stdio_client(server_params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        tools = await self._session.list_tools()
        self._tool_names = {_normalize_tool_key(tool.name): tool.name for tool in tools.tools}
        self._ready = True
        logger.info("MongoDB MCP session ready with tools: %s", sorted(self._tool_names.values()))

    async def close(self) -> None:
        self._ready = False
        self._session = None
        self._tool_names = {}
        await self._stack.aclose()

    async def call_tool(self, logical_name: str, arguments: dict[str, Any]) -> Any:
        if not self._session or not self._ready:
            raise RuntimeError("MongoDB MCP session is not ready")
        tool_name = self._resolve_tool(logical_name)
        return await self._session.call_tool(tool_name, arguments)

    def _resolve_tool(self, logical_name: str) -> str:
        key = _normalize_tool_key(logical_name)
        if key in self._tool_names:
            return self._tool_names[key]
        for alias in _tool_aliases().get(key, []):
            alias_key = _normalize_tool_key(alias)
            if alias_key in self._tool_names:
                return self._tool_names[alias_key]
        available = ", ".join(sorted(self._tool_names.values()))
        raise RuntimeError(f"MongoDB MCP tool '{logical_name}' not available. Found: {available}")


def _server_command() -> tuple[str, list[str]]:
    configured = os.getenv("MONGODB_MCP_COMMAND", "").strip()
    if configured:
        parts = configured.split()
        return parts[0], parts[1:]

    global_bin = shutil.which("mongodb-mcp-server")
    if global_bin:
        return global_bin, []

    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if npx:
        return npx, ["-y", "mongodb-mcp-server"]

    raise RuntimeError("mongodb-mcp-server is not installed and npx is unavailable")


def _normalize_tool_key(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _tool_aliases() -> dict[str, list[str]]:
    return {
        "find": ["find", "query"],
        "aggregate": ["aggregate"],
        "insert-many": ["insert-many", "insertmany", "insert"],
        "update-many": ["update-many", "updatemany", "update"],
        "list-databases": ["list-databases", "listdatabases"],
        "list-collections": ["list-collections", "listcollections"],
    }


def parse_tool_payload(result: Any) -> Any:
    if result is None:
        return None
    if hasattr(result, "structuredContent") and result.structuredContent is not None:
        return result.structuredContent
    content = getattr(result, "content", None) or []
    texts = [getattr(block, "text", "") for block in content if getattr(block, "text", None)]
    if not texts:
        return None
    joined = "\n".join(texts).strip()
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return joined


async def start_mcp_session() -> McpSessionManager:
    global _manager
    if _manager is not None and _manager.ready:
        return _manager
    manager = McpSessionManager()
    await manager.start()
    _manager = manager
    return manager


async def close_mcp_session() -> None:
    global _manager
    if _manager is None:
        return
    await _manager.close()
    _manager = None


def get_mcp_session() -> McpSessionManager | None:
    return _manager if _manager and _manager.ready else None


async def call_mcp_tool(logical_name: str, arguments: dict[str, Any]) -> Any:
    manager = get_mcp_session()
    if manager is None:
        raise RuntimeError("MongoDB MCP session is not initialized")
    result = await manager.call_tool(logical_name, arguments)
    return parse_tool_payload(result)
