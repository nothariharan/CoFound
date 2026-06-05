from __future__ import annotations

import asyncio
from zipfile import ZipFile

from agents import researcher
from agents.dialogue import synthesize_dialogue
from agents.diff_classifier import classify_pivot
from agents.export_agent import generate_export
from agents.growth_agent import recommend_priority
from agents.orchestrator import spawn_research_session
from critique.scorer import CritiqueResult
from graph.schema import NodeType


async def _deterministic_tools(query: str, tools: list[str]):
    return [
        {
            "tool": tool,
            "query": query,
            "items": [
                {
                    "source": tool,
                    "title": f"{tool} evidence for {query}",
                    "url": f"https://example.com/{tool}",
                    "snippet": "Evidence mentions urgent pain, existing spend, and competitor gaps.",
                }
            ],
            "sources": [tool],
        }
        for tool in (tools or ["exa"])
    ]


async def _accept(result, task):
    return CritiqueResult(score=85, verdict="accept", reason="specific evidence", accept=True)


async def _summary(prompt: str, system: str = "") -> str:
    return "Synthesized evidence: urgent customer pain, budget pressure, and reachable first segment."


def test_full_agent_lifecycle_without_external_services(monkeypatch, workspace, memory_store):
    monkeypatch.setattr(researcher, "execute_tools", _deterministic_tools)
    monkeypatch.setattr(researcher, "generate_flash", _summary)
    monkeypatch.setattr(researcher, "score_result", _accept)

    async def run():
        spawn = await spawn_research_session(workspace.idea_id, trigger="session_start", store=memory_store, run_inline=True)
        dialogue = await synthesize_dialogue(workspace.idea_id, memory_store)
        pivot = await classify_pivot(workspace.idea_id, "Pivot audience to ghost kitchens", memory_store, enqueue=True)
        priority = await recommend_priority(workspace.idea_id, memory_store)
        export = await generate_export(workspace.idea_id, memory_store)
        return spawn, dialogue, pivot, priority, export

    spawn, dialogue, pivot, priority, export = asyncio.run(run())

    assert spawn.tasks_queued >= 6
    researched_types = {node.type for node in workspace.nodes}
    assert {NodeType.AUDIENCE, NodeType.MARKET_INTELLIGENCE, NodeType.COMPETITORS}.issubset(researched_types)
    assert all(
        node.confidence >= 85
        for node in workspace.nodes
        if node.type in {NodeType.AUDIENCE, NodeType.MARKET_INTELLIGENCE, NodeType.COMPETITORS, NodeType.REVENUE, NodeType.PRODUCT_VISION, NodeType.TECH_STACK}
    )

    assert dialogue["question"].endswith("?")
    assert pivot["requery_needed"] is True
    assert set(pivot["nodes_affected"]) >= {"audience", "competitors", "revenue"}
    assert priority["action"]

    with ZipFile(export["path"]) as zf:
        assert len(zf.namelist()) >= 5
        assert "HANDOFF.md" in zf.namelist()
