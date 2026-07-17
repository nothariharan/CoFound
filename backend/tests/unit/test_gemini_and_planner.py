from __future__ import annotations

import asyncio
import json

from agents import planner
from llm.gemini import generate_flash, generate_pro


def test_gemini_mock_returns_planner_json_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    text = asyncio.run(generate_pro("Return JSON tasks", system="tasks json"))
    payload = json.loads(text)

    assert "tasks" in payload
    assert 6 <= len(payload["tasks"]) <= 10
    assert set(payload["tasks"][0]["tools"]).issubset({"reddit", "web", "firecrawl", "github"})


def test_gemini_mock_returns_critique_json_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    text = asyncio.run(generate_flash("Please critique and score this result", system="critique score"))
    payload = json.loads(text)

    assert payload["score"] == 82
    assert payload["accept"] is True


def test_planner_enqueues_valid_tasks_from_llm_json(monkeypatch, workspace, memory_store):
    async def fake_generate(prompt: str, system: str = "") -> str:
        return json.dumps(
            {
                "tasks": [
                    {"task": "Mine Reddit pain", "type": "audience", "tools": ["reddit"], "priority": 1},
                    {"task": "Map competitors", "type": "competitors", "tools": ["firecrawl"], "priority": 2},
                ]
            }
        )

    monkeypatch.setattr(planner, "generate_pro_resilient", fake_generate)

    tasks = asyncio.run(planner.plan(workspace, memory_store))

    assert [t.task for t in tasks] == ["Mine Reddit pain", "Map competitors"]
    assert [t.priority for t in memory_store.task_queue] == [1, 2]
    assert all(t.workspace_id == workspace.idea_id for t in tasks)


def test_planner_falls_back_when_llm_returns_invalid_json(monkeypatch, workspace, memory_store):
    async def bad_generate(prompt: str, system: str = "") -> str:
        return "not-json"

    monkeypatch.setattr(planner, "generate_pro_resilient", bad_generate)

    tasks = asyncio.run(planner.plan(workspace, memory_store))

    assert len(tasks) == 6
    assert tasks[0].type == "audience"
    assert tasks[-1].type == "tech_stack"


def test_planner_sanitizes_malformed_llm_fields(monkeypatch, workspace, memory_store):
    async def malformed_generate(prompt: str, system: str = "") -> str:
        return json.dumps({"tasks": [{"task": "Bad fields", "type": "made_up", "tools": "exa reddit", "priority": "urgent"}]})

    monkeypatch.setattr(planner, "generate_pro_resilient", malformed_generate)

    tasks = asyncio.run(planner.plan(workspace, memory_store))

    assert len(tasks) == 1
    assert tasks[0].type == "market_intelligence"
    assert tasks[0].tools == ["web", "reddit"]
    assert tasks[0].priority == 1
