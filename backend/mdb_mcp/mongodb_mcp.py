"""MongoDB MCP configuration for the CoFound cluster."""

from __future__ import annotations

import os


def get_mcp_connection_string() -> str:
    return (
        os.getenv("MDB_MCP_CONNECTION_STRING", "").strip()
        or os.getenv("MONGODB_URI", "").strip()
    )


def mcp_cluster_label() -> str:
    uri = get_mcp_connection_string()
    if "cofound." in uri.lower():
        return "CoFound"
    if uri:
        return "configured"
    return "not-configured"
