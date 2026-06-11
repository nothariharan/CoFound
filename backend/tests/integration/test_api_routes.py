from __future__ import annotations

import asyncio

from api import agents as agents_api
from api import export as export_api
from api import workspace as workspace_api
from agents.orchestrator import OrchestratorResult
from agents.store_protocol import ResearchTask
from graph.schema import BaseNode, NodeType, WorkspaceCreateRequest, canonical_node_id
from main import app


def test_spawn_agents_route_returns_contract(monkeypatch, workspace):
    async def fake_spawn(workspace_id: str, trigger: str, store):
        return OrchestratorResult(session_id="session-1", tasks_queued=8, agents_active=2, tasks=[])

    monkeypatch.setattr(agents_api, "spawn_research_session", fake_spawn)

    response = asyncio.run(agents_api.spawn_agents(agents_api.SpawnRequest(workspace_id=workspace.idea_id, trigger="manual")))

    assert response.model_dump() == {"session_id": "session-1", "tasks_queued": 8, "agents_active": 2}


def test_pivot_route_returns_contract(monkeypatch, workspace):
    async def fake_classify(workspace_id: str, message: str, store, enqueue: bool):
        assert enqueue is False
        return {"nodes_affected": ["audience"], "nodes_unchanged": ["core_idea"], "requery_needed": True, "spawn_researcher": True}

    monkeypatch.setattr(agents_api, "classify_pivot", fake_classify)

    response = asyncio.run(agents_api.pivot_agents(agents_api.PivotRequest(workspace_id=workspace.idea_id, message="pivot")))

    assert response["nodes_affected"] == ["audience"]
    assert response["spawn_researcher"] is True


def test_research_node_route_queues_one_approved_node(monkeypatch, workspace, memory_store):
    agents_api.DEFAULT_STORE.set(memory_store)
    workspace.nodes[0].confidence = 70
    workspace.nodes.append(
        BaseNode(
            node_id=canonical_node_id(NodeType.AUDIENCE),
            type=NodeType.AUDIENCE,
            title="Audience",
            summary="Approve audience research.",
        )
    )

    async def fake_run_researchers(workspace_id: str, store, worker_count: int, session_id=None):
        assert workspace_id == workspace.idea_id
        assert worker_count == 1

    monkeypatch.setattr(agents_api, "run_researchers", fake_run_researchers)

    response = asyncio.run(
        agents_api.research_node(
            agents_api.ResearchNodeRequest(workspace_id=workspace.idea_id, node_type=NodeType.AUDIENCE)
        )
    )

    assert response.tasks_queued == 1
    assert response.agents_active == 1
    assert [task.type for task in memory_store.task_queue] == ["audience"]


def test_workspace_create_frames_without_starting_research(monkeypatch, memory_store):
    workspace_api.DEFAULT_STORE.set(memory_store)
    async def fake_frame(idea: str):
        return {
            "workspace_name": "KitchenOps Copilot",
            "core_title": "Restaurant Waste Copilot",
            "problem": "Restaurants waste inventory.",
            "solution": "Predict stock needs.",
            "one_liner": "AI inventory planning for restaurants.",
            "confidence": 72,
        }

    monkeypatch.setattr(workspace_api, "frame_idea", fake_frame)

    response = asyncio.run(
        workspace_api.create_workspace(
            WorkspaceCreateRequest(idea="AI copilot for restaurant owners to manage inventory and reduce waste")
        )
    )

    assert response.workspace_name == "KitchenOps Copilot"
    assert response.nodes[0]["title"] == "Restaurant Waste Copilot"
    assert response.nodes[0]["confidence"] == 72
    assert memory_store.task_queue == []


def test_main_app_includes_track_b_routers():
    paths = {route.path for route in app.routes}

    assert "/api/agents/spawn" in paths
    assert "/api/agents/research-node" in paths
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
