"""agent store selector — hybrid mcp for agents, atlas/memory for api routes"""
from __future__ import annotations

import logging
import os

from agents.store_protocol import DEFAULT_STORE, GraphStore

logger = logging.getLogger(__name__)

_agent_store: GraphStore | None = None
_agent_store_mode = "default"


def use_mongodb_mcp_enabled() -> bool:
    explicit = os.getenv("USE_MONGODB_MCP", "").strip().lower()
    if explicit in {"0", "false", "no", "off"}:
        return False
    if explicit in {"1", "true", "yes", "on"}:
        return True
    from mdb_mcp.mongodb_mcp import get_mcp_connection_string

    return bool(get_mcp_connection_string().strip())


def set_agent_store(store: GraphStore, mode: str = "mcp") -> None:
    global _agent_store, _agent_store_mode
    _agent_store = store
    _agent_store_mode = mode
    logger.info("Agent store mode set to %s", mode)


def agent_store_mode() -> str:
    return _agent_store_mode


def get_agent_store() -> GraphStore:
    if _agent_store is not None:
        return _agent_store
    return DEFAULT_STORE.get()
