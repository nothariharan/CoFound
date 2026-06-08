from __future__ import annotations

import asyncio

from api import agents as agents_api
from api import export as export_api
from agents.orchestrator import OrchestratorResult
from agents.store_protocol import ResearchTask
from main import app


def test_spawn_agents_route_returns_contract(monkeypatch, workspace):
    async def fake_spawn(workspace_id: str, trigger: str, store):
        return OrchestratorResult(session_id="session-1", tasks_queued=8, agents_active=2, tasks=[])

    monkeypatch.setattr(agents_api, "spawn_research_session", fake_spawn)

    response = asyncio.run(agents_api.spawn_agents(agents_api.SpawnRequest(workspace_id=workspace.idea_id, trigger="manual")))

    assert response.model_dump() == {"session_id": "session-1", "tasks_queued": 8, "agents_active": 2}


def test_pivot_route_returns_contract(monkeypatch, workspace):
    async def fake_classify(workspace_id: str, message: str, store, enqueue: bool):
        return {"nodes_affected": ["audience"], "nodes_unchanged": ["core_idea"], "requery_needed": True, "spawn_researcher": True}

    monkeypatch.setattr(agents_api, "classify_pivot", fake_classify)

    response = asyncio.run(agents_api.pivot_agents(agents_api.PivotRequest(workspace_id=workspace.idea_id, message="pivot")))

    assert response["nodes_affected"] == ["audience"]
    assert response["spawn_researcher"] is True


def test_main_app_includes_track_b_routers():
    paths = {route.path for route in app.routes}

    assert "/api/agents/spawn" in paths
    assert "/api/agents/pivot" in paths
    assert "/api/agents/dialogue" in paths
    assert "/api/agents/observe" in paths
    assert "/api/agents/observe-funnel" in paths
    assert "/api/priority" in paths
    assert "/api/nodes/{node_id}" in paths
    assert "/api/workspace/{idea_id}/journal" in paths
    assert "/api/integrations" in paths
    assert "/api/integrations/github" in paths
    assert "/api/integrations/posthog" in paths
    assert "/api/export" in paths
    assert "/api/export/{export_id}/download" in paths


def test_export_route_returns_download_url(monkeypatch, workspace):
    async def fake_export(workspace_id: str, store):
        return {"export_url": "/api/export/export-1/download", "files": ["README.md", "HANDOFF.md"]}

    monkeypatch.setattr(export_api, "generate_export", fake_export)

    response = asyncio.run(export_api.export_workspace(export_api.ExportRequest(workspace_id=workspace.idea_id)))

    assert response == {"export_url": "/api/export/export-1/download", "files": ["README.md", "HANDOFF.md"]}
