from __future__ import annotations

import asyncio
import json
from zipfile import ZipFile

from agents import diff_classifier, orchestrator, planner, researcher
from agents.diff_classifier import classify_pivot
from agents.export_agent import generate_export
from agents.growth_agent import recommend_priority
from agents.observe_agent import observe_funnel
from critique.scorer import CritiqueResult


async def _fake_tools(query: str, tools: list[str]):
    return [{"tool": "exa", "items": [{"source": "exa", "title": "signal", "url": "https://example.com"}], "sources": ["exa"]}]


async def _fake_summary(prompt: str, system: str = "") -> str:
    return "Strong signal: customers need this and competitors leave a gap."


def test_orchestrator_plans_and_runs_research_inline(monkeypatch, workspace, memory_store):
    async def fake_plan(ws, store):
        task = planner.ResearchTask(workspace_id=ws.idea_id, task="Find competitors", type="competitors", tools=["exa"], priority=1)
        await store.enqueue_task(task)
        return [task]

    async def accept(result, task):
        return CritiqueResult(score=86, verdict="accept", reason="specific", accept=True)

    monkeypatch.setattr(orchestrator, "plan", fake_plan)
    monkeypatch.setattr(researcher, "execute_tools", _fake_tools)
    monkeypatch.setattr(researcher, "generate_flash", _fake_summary)
    monkeypatch.setattr(researcher, "score_result", accept)

    result = asyncio.run(orchestrator.spawn_research_session(workspace.idea_id, store=memory_store, run_inline=True))

    assert result.tasks_queued == 1
    assert result.agents_active == 1
    assert any(n.type.value == "competitors" and n.confidence == 86 for n in workspace.nodes)


def test_diff_classifier_returns_contract_and_enqueues_affected_nodes(monkeypatch, workspace, memory_store):
    async def fake_generate(prompt: str, system: str = "") -> str:
        return json.dumps(
            {
                "nodes_affected": ["audience", "competitors", "revenue"],
                "nodes_unchanged": ["core_idea", "tech_stack"],
                "requery_needed": True,
                "spawn_researcher": True,
            }
        )

    monkeypatch.setattr(diff_classifier, "generate_pro", fake_generate)

    result = asyncio.run(classify_pivot(workspace.idea_id, "Actually pivot to ghost kitchens", memory_store, enqueue=True))

    assert result == {
        "nodes_affected": ["audience", "competitors", "revenue"],
        "nodes_unchanged": ["core_idea", "tech_stack"],
        "requery_needed": True,
        "spawn_researcher": True,
    }
    assert [task.type for task in memory_store.task_queue] == ["audience", "competitors", "revenue"]


def test_diff_classifier_respects_string_false_booleans(monkeypatch, workspace, memory_store):
    async def fake_generate(prompt: str, system: str = "") -> str:
        return json.dumps(
            {
                "nodes_affected": ["audience"],
                "nodes_unchanged": ["core_idea"],
                "requery_needed": "false",
                "spawn_researcher": "false",
            }
        )

    monkeypatch.setattr(diff_classifier, "generate_pro", fake_generate)

    result = asyncio.run(classify_pivot(workspace.idea_id, "Minor wording change", memory_store, enqueue=True))

    assert result["requery_needed"] is False
    assert result["spawn_researcher"] is False
    assert memory_store.task_queue == []


def test_growth_priority_uses_lowest_confidence_node(workspace, memory_store, monkeypatch):
    async def bad_json(prompt: str, system: str = "") -> str:
        return "not json"

    monkeypatch.setattr("agents.growth_agent.generate_pro", bad_json)

    result = asyncio.run(recommend_priority(workspace.idea_id, memory_store))

    assert "action" in result
    assert result["estimated_time"] == "~2 hrs"
    assert "Core Idea" in result["reason"] or "core idea" in result["reason"]


def test_observe_funnel_triggers_growth_when_drop_detected(workspace, memory_store, monkeypatch):
    async def bad_json(prompt: str, system: str = "") -> str:
        return "not json"

    monkeypatch.setattr("agents.growth_agent.generate_pro", bad_json)

    result = asyncio.run(observe_funnel(workspace.idea_id, memory_store))

    assert result["drops"]
    assert "growth_recommendation" in result
    assert any(node.type.value == "observe" for node in workspace.nodes)
    assert any(node.type.value == "growth" for node in workspace.nodes)


def test_export_agent_creates_zip_with_required_files(workspace, memory_store, monkeypatch):
    async def mock_export(prompt: str, system: str = "") -> str:
        return "Mock Gemini response: force fallback"

    monkeypatch.setattr("export.generator.generate_pro", mock_export)

    result = asyncio.run(generate_export(workspace.idea_id, memory_store))

    assert result["export_url"].startswith("/api/export/")
    assert set(result["files"]) >= {"README.md", "tech_stack.md", "ui_spec.md", ".cursorrules", "HANDOFF.md"}
    with ZipFile(result["path"]) as zf:
        names = set(zf.namelist())
        assert set(result["files"]) == names
        readme = zf.read("README.md").decode()
        assert workspace.workspace_name in readme
        assert "Startup Graph Summary" in readme
