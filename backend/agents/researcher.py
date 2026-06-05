"""Karpathy self-critique research loop — spawned N times by orchestrator."""

from __future__ import annotations

import asyncio
from typing import Any

from agents.store_protocol import DEFAULT_STORE, GraphStore, ResearchTask
from critique.scorer import score as score_result
from graph.schema import BaseNode, UnlockConditions, status_from_confidence
from llm.gemini import generate_flash
from sse.feed import feed
from tools import exa_search, firecrawl, github_search, gummysearch, producthunt, reddit_praw

RESEARCH_SYSTEM = """You are a concise research synthesis agent.
Given raw tool JSON, return a compact evidence summary with customer pains,
competitors, risks, and recommended graph update. No fluff.
"""


async def run_researchers(workspace_id: str, store: GraphStore = DEFAULT_STORE, worker_count: int = 2, session_id: str | None = None) -> None:
    workers = [asyncio.create_task(research_loop(workspace_id, store, name=f"R{i+1}")) for i in range(worker_count)]
    await asyncio.gather(*workers)
    await feed.publish(workspace_id, {"text": "[Orchestrator] Research session complete.", "type": "done"})


async def research_loop(workspace_id: str, store: GraphStore = DEFAULT_STORE, name: str = "R1") -> None:
    while True:
        task = await store.pop_pending_task(workspace_id)
        if task is None:
            return
        await _run_task(workspace_id, store, task, name)


async def _run_task(workspace_id: str, store: GraphStore, task: ResearchTask, name: str) -> None:
    query = task.query or task.task
    while task.attempts <= task.max_attempts:
        await feed.publish(workspace_id, {"text": f"[Researcher {name}] Running {', '.join(task.tools) or 'exa'} scan: {query}", "type": "info", "node_id": task.node_id})
        try:
            raw = await execute_tools(query, task.tools)
            result = await synthesize_result(task, raw)
            critique = await score_result(result, task.task)
        except Exception as exc:
            reason = f"Research task failed: {exc}"
            task.status = "failed"
            task.last_error = reason
            await store.log_dead_end(workspace_id, task.task, reason)
            await feed.publish(workspace_id, {"text": f"[Researcher {name}] Dead end: {reason}", "type": "error", "node_id": task.node_id})
            return
        await feed.publish(
            workspace_id,
            {"text": f"[Critique: {critique.score}/100] {critique.reason}", "type": "critique", "node_id": task.node_id, "score": critique.score},
        )

        if critique.score >= 80 and critique.accept:
            await _commit(store, workspace_id, task, result, critique.score)
            await store.mark_task_done(task.task_id, critique.score)
            await feed.publish(workspace_id, {"text": f"[Researcher {name}] Accepted and committed: {task.type}", "type": "done", "node_id": task.node_id})
            return

        if 50 <= critique.score < 80 and task.attempts < task.max_attempts:
            task.attempts += 1
            query = critique.requery or f"{query} specific evidence customer urgency"
            await feed.publish(workspace_id, {"text": f"[Researcher {name}] Soft reset → refining query (attempt {task.attempts}/{task.max_attempts}).", "type": "info", "node_id": task.node_id})
            continue

        reason = critique.reason or "Research score below acceptance threshold."
        task.status = "failed"
        task.last_error = reason
        await store.log_dead_end(workspace_id, task.task, reason)
        await feed.publish(workspace_id, {"text": f"[Researcher {name}] Dead end: {reason}", "type": "error", "node_id": task.node_id})
        return


async def execute_tools(query: str, tools: list[str]) -> list[dict[str, Any]]:
    selected = tools or ["exa", "reddit"]
    calls: list[tuple[str, Any]] = []
    for tool in selected:
        tool = str(tool).lower().strip()
        if tool == "reddit":
            calls.append((tool, reddit_praw.search(query, limit=5)))
        elif tool == "firecrawl":
            calls.append((tool, firecrawl.scrape(query, limit=3)))
        elif tool == "github":
            calls.append((tool, github_search.search_repositories(query, limit=5)))
        elif tool == "exa":
            calls.append((tool, exa_search.search(query, num_results=5)))
        elif tool == "gummysearch":
            calls.append((tool, gummysearch.search_pain_points(query, limit=5)))
        elif tool in {"producthunt", "product_hunt"}:
            calls.append((tool, producthunt.search_launches(query, limit=5)))
    if not calls:
        calls = [("exa", exa_search.search(query, num_results=5)), ("reddit", reddit_praw.search(query, limit=5))]

    gathered = await asyncio.gather(*(call for _, call in calls), return_exceptions=True)
    results: list[dict[str, Any]] = []
    for (tool, _), value in zip(calls, gathered, strict=True):
        if isinstance(value, Exception):
            results.append({"tool": tool, "query": query, "items": [], "sources": [tool], "error": str(value)})
        else:
            results.append(value)
    return results


async def synthesize_result(task: ResearchTask, raw: list[dict[str, Any]]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    sources: set[str] = set()
    for block in raw:
        items.extend(block.get("items") or [])
        sources.update(block.get("sources") or ([block.get("tool")] if block.get("tool") else []))
    prompt = {"task": task.model_dump(mode="json"), "raw_results": raw[:4]}
    try:
        summary = await generate_flash(str(prompt)[:12000], system=RESEARCH_SYSTEM)
    except Exception:
        summary = _fallback_summary(task, items)
    return {"task": task.task, "type": task.type, "summary": summary, "items": items[:20], "sources": sorted(s for s in sources if s), "raw": raw}


async def _commit(store: GraphStore, workspace_id: str, task: ResearchTask, result: dict[str, Any], score: int) -> None:
    if hasattr(store, "commit_research_result"):
        await getattr(store, "commit_research_result")(workspace_id, task, result, score)
        return
    # Atlas GraphStore may not expose a helper; update an existing matching node if present.
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    node_type = task.type
    existing = next((n for n in workspace.nodes if n.type.value == node_type), None)
    confidence = max(score, existing.confidence if existing else 0)
    if existing:
        node = existing.model_copy(deep=True)
    else:
        node = BaseNode(
            type=node_type,
            title=node_type.replace("_", " ").title(),
            unlock_conditions=UnlockConditions(),
        )
    node.confidence = confidence
    node.status = status_from_confidence(confidence)
    node.agent_notes = result.get("summary", "")[:2000]
    node.summary = node.agent_notes[:240]
    node.sources = sorted(set(node.sources + result.get("sources", [])))
    node.research_history.append({"task": task.task, "score": score, "result": result})
    await store.update_node(workspace_id, node)


def _fallback_summary(task: ResearchTask, items: list[dict[str, Any]]) -> str:
    titles = "; ".join(str(i.get("title") or i.get("snippet") or "evidence") for i in items[:3])
    return f"Research for {task.type}: {titles or 'no high-quality evidence found yet.'}"
