from __future__ import annotations

import asyncio

from graph.schema import WorkspaceDocument, create_core_idea_node
from mdb_mcp.graph_store import McpGraphStore


def test_mcp_graph_store_get_workspace_parses_find_result(monkeypatch):
    workspace = WorkspaceDocument(
        idea_id="idea-123",
        workspace_name="Test Workspace",
        nodes=[create_core_idea_node("AI copilot for restaurants")],
    )
    payload = workspace.model_dump(mode="json")

    async def fake_find_one(collection, *, filter, projection=None, sort=None):
        assert collection == "startup_graphs"
        assert filter == {"idea_id": "idea-123"}
        return payload

    monkeypatch.setattr("mdb_mcp.graph_store.db_ops.mcp_find_one", fake_find_one)

    async def run():
        store = McpGraphStore()
        return await store.get_workspace("idea-123")

    loaded = asyncio.run(run())

    assert loaded is not None
    assert loaded.idea_id == "idea-123"
    assert loaded.workspace_name == "Test Workspace"
    assert loaded.nodes[0].type.value == "core_idea"


def test_mcp_graph_store_search_knowledge_base_uses_aggregate(monkeypatch):
    calls: list[str] = []

    async def fake_aggregate(collection, pipeline):
        calls.append(collection)
        return [{"title": "PMF", "snippet": "Validate painful problems"}]

    async def fake_find(*args, **kwargs):
        return []

    monkeypatch.setattr("mdb_mcp.graph_store.db_ops.mcp_aggregate", fake_aggregate)
    monkeypatch.setattr("mdb_mcp.graph_store.db_ops.mcp_find", fake_find)

    async def run():
        store = McpGraphStore()
        return await store.search_knowledge_base("product market fit", limit=3)

    results = asyncio.run(run())

    assert calls == ["product_knowledge_base"]
    assert results[0]["title"] == "PMF"
