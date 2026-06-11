from __future__ import annotations

import asyncio
import json

from agents import planner
from agents.adk import planner_agent as adk_planner_module
from agents.adk.runner import run_planner_agent
from agents.adk.vertex_deploy import deployment_status


def test_adk_planner_agent_uses_google_adk():
    assert adk_planner_module.planner_agent.name == "cofounder_planner"
    assert "gemini" in adk_planner_module.planner_agent.model


def test_vertex_deploy_status_documents_billing_gate():
    status = deployment_status()
    assert status["framework"] == "google-adk"
    assert status["billing_required"] == "true"
    assert status["vertex_enabled"] == "false"


def test_planner_enqueues_valid_tasks_from_adk_json(monkeypatch, workspace, memory_store):
    async def fake_adk(prompt: str) -> str:
        return json.dumps(
            {
                "tasks": [
                    {"task": "Mine Reddit pain", "type": "audience", "tools": ["reddit"], "priority": 1},
                    {"task": "Map competitors", "type": "competitors", "tools": ["firecrawl"], "priority": 2},
                ]
            }
        )

    monkeypatch.setattr(planner, "run_planner_agent", fake_adk)

    tasks = asyncio.run(planner.plan(workspace, memory_store))

    assert [t.task for t in tasks] == ["Mine Reddit pain", "Map competitors"]
    assert [t.priority for t in memory_store.task_queue] == [1, 2]


def test_planner_falls_back_when_adk_returns_invalid_json(monkeypatch, workspace, memory_store):
    async def bad_adk(prompt: str) -> str:
        return "not-json"

    monkeypatch.setattr(planner, "run_planner_agent", bad_adk)

    tasks = asyncio.run(planner.plan(workspace, memory_store))

    assert len(tasks) == 6
    assert tasks[0].type == "audience"


def test_run_planner_agent_requires_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    try:
        asyncio.run(run_planner_agent('{"workspace": {}}'))
        raised = False
    except RuntimeError as exc:
        raised = True
        assert "GOOGLE_API_KEY" in str(exc)

    assert raised
