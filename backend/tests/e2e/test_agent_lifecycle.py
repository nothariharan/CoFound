from __future__ import annotations

import asyncio
from zipfile import ZipFile

from agents import dialogue, researcher
from agents.dialogue import synthesize_dialogue
from agents.diff_classifier import classify_pivot
from agents.export_agent import generate_export
from agents.growth_agent import recommend_priority
from agents.researcher import run_researchers
from agents.store_protocol import ResearchTask
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


async def _dialogue_json(prompt: str, system: str = "") -> str:
    return '{"brief":"Synthesized graph brief.","question":"Which customer segment will you interview first?"}'


def test_full_agent_lifecycle_without_external_services(monkeypatch, workspace, memory_store):
    monkeypatch.setattr(researcher, "execute_tools", _deterministic_tools)
    monkeypatch.setattr(researcher, "generate_flash", _summary)
    monkeypatch.setattr(researcher, "score_result", _accept)
    monkeypatch.setattr(dialogue, "generate_pro", _dialogue_json)

    async def run():
        await memory_store.enqueue_task(
            ResearchTask(
                workspace_id=workspace.idea_id,
                task="Research audience after user approval",
                type="audience",
                tools=["reddit", "firecrawl"],
                priority=1,
            )
        )
        await run_researchers(workspace.idea_id, store=memory_store, worker_count=1)
        dialogue_result = await synthesize_dialogue(workspace.idea_id, memory_store)
        pivot = await classify_pivot(workspace.idea_id, "Pivot audience to ghost kitchens", memory_store, enqueue=False)
        priority = await recommend_priority(workspace.idea_id, memory_store)
        export = await generate_export(workspace.idea_id, memory_store)
        return dialogue_result, pivot, priority, export

    dialogue_result, pivot, priority, export = asyncio.run(run())

    researched_types = {node.type for node in workspace.nodes}
    assert NodeType.AUDIENCE in researched_types
    assert dialogue_result["question"].endswith("?")
    assert pivot["requery_needed"] is True
    assert set(pivot["nodes_affected"]) >= {"audience", "competitors", "revenue"}
    affected_types = {NodeType(node_type) for node_type in pivot["nodes_affected"]}
    assert all(node.confidence == 0 for node in workspace.nodes if node.type in affected_types and node.type != NodeType.CORE_IDEA)
    assert all(task.status == "done" for task in memory_store.task_queue)
    assert priority["action"]

    with ZipFile(export["path"]) as zf:
        assert len(zf.namelist()) >= 5
        assert "HANDOFF.md" in zf.namelist()
