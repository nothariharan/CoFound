from __future__ import annotations

import asyncio

from agents import researcher
from agents.store_protocol import ResearchTask
from critique.scorer import CritiqueResult
from graph.schema import BaseNode


async def _fake_tools(query: str, tools: list[str]):
    return [
        {
            "tool": "reddit",
            "query": query,
            "items": [{"source": "reddit", "title": "pain", "url": "https://reddit.com/x"}],
            "sources": ["reddit"],
        },
        {
            "tool": "exa",
            "query": query,
            "items": [{"source": "exa", "title": "market", "url": "https://example.com/y"}],
            "sources": ["exa"],
        },
    ]


async def _fake_generate(prompt: str, system: str = "") -> str:
    return "Evidence summary with pain, market signal, and next action."


def test_researcher_accepts_and_commits_result(monkeypatch, memory_store, workspace):
    async def accept(result, task):
        return CritiqueResult(score=88, verdict="accept", reason="specific", accept=True)

    monkeypatch.setattr(researcher, "execute_tools", _fake_tools)
    monkeypatch.setattr(researcher, "generate_flash", _fake_generate)
    monkeypatch.setattr(researcher, "score_result", accept)

    async def run():
        task = ResearchTask(workspace_id=workspace.idea_id, task="Find audience pain", type="audience", tools=["reddit", "exa"], priority=1)
        await memory_store.enqueue_task(task)
        await researcher.research_loop(workspace.idea_id, memory_store, name="T1")
        return task

    task = asyncio.run(run())

    assert task.status == "done"
    assert len(workspace.nodes) == 2
    audience = next(n for n in workspace.nodes if n.type.value == "audience")
    assert audience.confidence == 88
    assert sorted(audience.sources) == ["exa", "reddit"]


def test_researcher_soft_resets_then_accepts(monkeypatch, memory_store, workspace):
    scores = [CritiqueResult(score=63, verdict="refine", reason="Too broad", requery="narrow query", accept=False), CritiqueResult(score=84, verdict="accept", reason="specific", accept=True)]

    async def score_sequence(result, task):
        return scores.pop(0)

    monkeypatch.setattr(researcher, "execute_tools", _fake_tools)
    monkeypatch.setattr(researcher, "generate_flash", _fake_generate)
    monkeypatch.setattr(researcher, "score_result", score_sequence)

    async def run():
        task = ResearchTask(workspace_id=workspace.idea_id, task="Validate pricing", type="revenue", tools=["reddit"], priority=1)
        await memory_store.enqueue_task(task)
        await researcher.research_loop(workspace.idea_id, memory_store, name="T1")
        return task

    task = asyncio.run(run())

    assert task.status == "done"
    assert task.attempts == 2
    assert any(n.type.value == "revenue" and n.confidence == 84 for n in workspace.nodes)


def test_execute_tools_returns_error_blocks_for_tool_exceptions(monkeypatch):
    async def broken_search(query: str, limit: int = 5):
        raise RuntimeError("reddit down")

    monkeypatch.setattr(researcher.reddit_praw, "search", broken_search)

    results = asyncio.run(researcher.execute_tools("inventory", ["reddit"]))

    assert results == [{"tool": "reddit", "query": "inventory", "items": [], "sources": ["reddit"], "error": "reddit down"}]


def test_commit_fallback_creates_matching_node_instead_of_overwriting_core(workspace):
    class MinimalStore:
        def __init__(self, ws):
            self.ws = ws

        async def get_workspace(self, workspace_id: str):
            return self.ws

        async def update_node(self, workspace_id: str, node: BaseNode):
            self.ws.nodes.append(node)
            return node

    task = ResearchTask(workspace_id=workspace.idea_id, task="Find audience", type="audience", tools=["exa"], priority=1)

    asyncio.run(researcher._commit(MinimalStore(workspace), workspace.idea_id, task, {"summary": "audience evidence", "sources": ["exa"]}, 83))

    assert workspace.nodes[0].type.value == "core_idea"
    assert any(node.type.value == "audience" and node.confidence == 83 for node in workspace.nodes)


def test_researcher_logs_dead_end_after_hard_reject(monkeypatch, memory_store, workspace):
    async def reject(result, task):
        return CritiqueResult(score=22, verdict="reject", reason="no evidence", accept=False)

    monkeypatch.setattr(researcher, "execute_tools", _fake_tools)
    monkeypatch.setattr(researcher, "generate_flash", _fake_generate)
    monkeypatch.setattr(researcher, "score_result", reject)

    async def run():
        task = ResearchTask(workspace_id=workspace.idea_id, task="Bad query", type="competitors", tools=["exa"], priority=1)
        await memory_store.enqueue_task(task)
        await researcher.research_loop(workspace.idea_id, memory_store, name="T1")
        return task

    task = asyncio.run(run())

    assert task.status == "failed"
    assert memory_store.dead_ends[0]["task"] == "Bad query"
    assert len(workspace.nodes) == 1
