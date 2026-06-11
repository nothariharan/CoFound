from __future__ import annotations

import asyncio
import sys
import types

from agents import researcher
from agents.store_protocol import ResearchTask
from critique.scorer import CritiqueResult
from graph.schema import BaseNode
from tools import scrapling_web


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


def test_execute_tools_routes_broad_aliases_to_scrapling(monkeypatch):
    async def fake_broad(query: str, limit: int = 5):
        return {
            "tool": "scrapling",
            "query": query,
            "items": [{"source": "web", "origin": "reddit", "title": "pain", "url": "https://reddit.com/r/test"}],
            "sources": ["scrapling", "web"],
        }

    monkeypatch.setattr(researcher.scrapling_web, "search_broad", fake_broad)

    results = asyncio.run(researcher.execute_tools("pricing pain", ["scrapling", "exa", "gummysearch"]))

    assert [result["tool"] for result in results] == ["scrapling", "scrapling", "scrapling"]
    assert all(result["items"][0]["url"] for result in results)


def test_scrapling_fetch_tiered_escalates_to_stealth(monkeypatch):
    calls: list[str] = []

    class EmptySession:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, *args, **kwargs):
            calls.append("http")
            return ""

    class Stealthy:
        @staticmethod
        def fetch(*args, **kwargs):
            calls.append("stealth")
            return "This page has enough text to count as a successful browser fallback. " * 3

    fetchers = types.ModuleType("scrapling.fetchers")
    fetchers.FetcherSession = EmptySession
    fetchers.StealthyFetcher = Stealthy
    scrapling = types.ModuleType("scrapling")
    scrapling.fetchers = fetchers
    monkeypatch.setitem(sys.modules, "scrapling", scrapling)
    monkeypatch.setitem(sys.modules, "scrapling.fetchers", fetchers)

    page = scrapling_web._fetch_tiered("https://example.com")

    assert "successful browser fallback" in str(page)
    assert calls == ["http", "stealth"]


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
    competitors = next(node for node in workspace.nodes if node.type.value == "competitors")
    assert competitors.confidence == 0
    assert competitors.active_agents == []
    assert competitors.research_history[-1]["status"] == "failed"
    assert any(entry["event"] == "research_dead_end" for entry in memory_store.journal_entries)


def test_researcher_commits_final_near_threshold_result_as_partial(monkeypatch, memory_store, workspace):
    workspace.nodes[0].confidence = 70

    async def near_threshold(result, task):
        return CritiqueResult(score=79, verdict="refine", reason="specific but needs more proof", accept=False)

    monkeypatch.setattr(researcher, "execute_tools", _fake_tools)
    monkeypatch.setattr(researcher, "generate_flash", _fake_generate)
    monkeypatch.setattr(researcher, "score_result", near_threshold)

    async def run():
        task = ResearchTask(workspace_id=workspace.idea_id, task="Research market intelligence", type="market_intelligence", tools=["reddit", "exa"], priority=1)
        await memory_store.enqueue_task(task)
        await researcher.research_loop(workspace.idea_id, memory_store, name="T1")
        return task

    task = asyncio.run(run())

    market = next(node for node in workspace.nodes if node.type.value == "market_intelligence")
    assert task.status == "done"
    assert market.confidence == 79
    assert market.status.value == "needs_work"
    assert market.research_history[-1]["status"] == "partial"
    assert "Needs more validation" in market.agent_notes
