"""Karpathy self-critique research loop — spawned N times by orchestrator."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from agents.store_protocol import GraphStore, ResearchTask
from mdb_mcp.agent_store import get_agent_store
from critique.scorer import score as score_result
from graph.schema import BaseNode, NodeStatus, NodeType, UnlockConditions, node_agent_id, status_from_confidence
from llm.gemini import generate_flash
from sse.feed import feed
from tools import firecrawl, github_search, reddit_praw, scrapling_web

RESEARCH_SYSTEM = """You are a concise research synthesis agent.
Given raw tool JSON, return a compact evidence summary with customer pains,
competitors, risks, and recommended graph update. No fluff.
"""


async def run_researchers(workspace_id: str, store: GraphStore | None = None, worker_count: int = 2, session_id: str | None = None) -> None:
    store = store or get_agent_store()
    workers = [asyncio.create_task(research_loop(workspace_id, store, name=f"R{i+1}")) for i in range(worker_count)]
    await asyncio.gather(*workers)
    await feed.publish(workspace_id, {"text": "[Orchestrator] Research session complete.", "type": "done"})


async def research_loop(workspace_id: str, store: GraphStore | None = None, name: str = "R1") -> None:
    store = store or get_agent_store()
    while True:
        task = await store.pop_pending_task(workspace_id)
        if task is None:
            return
        await _run_task(workspace_id, store, task, name)


async def _run_task(workspace_id: str, store: GraphStore, task: ResearchTask, name: str) -> None:
    query = task.query or task.task
    last_result: dict[str, Any] | None = None
    last_score = 0
    await _mark_progress(workspace_id, store, task, name, f"Starting {', '.join(task.tools) or 'firecrawl, reddit'} research.")
    while task.attempts <= task.max_attempts:
        await _mark_progress(
            workspace_id,
            store,
            task,
            name,
            f"Attempt {max(1, task.attempts)}/{task.max_attempts}: scanning {', '.join(task.tools) or 'firecrawl, reddit'} for: {query}",
        )
        await feed.publish(workspace_id, {"text": f"[Researcher {name}] Running {', '.join(task.tools) or 'firecrawl, reddit'} scan: {query}", "type": "info", "node_id": task.node_id})
        try:
            raw = await execute_tools(query, task.tools)
            result = await synthesize_result(task, raw)
            critique = await score_result(result, task.task)
            last_result = result
            last_score = critique.score
        except Exception as exc:
            reason = f"Research task failed: {exc}"
            task.status = "failed"
            task.last_error = reason
            await store.log_dead_end(workspace_id, task.task, reason)
            await _mark_failure(workspace_id, store, task, reason)
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
            await _mark_progress(workspace_id, store, task, name, f"Refining query after {critique.score}/100: {critique.reason}")
            await feed.publish(workspace_id, {"text": f"[Researcher {name}] Soft reset → refining query (attempt {task.attempts}/{task.max_attempts}).", "type": "info", "node_id": task.node_id})
            continue

        reason = critique.reason or "Research score below acceptance threshold."
        if last_result is not None and _should_commit_partial(last_result, last_score):
            partial = dict(last_result)
            partial["summary"] = f"Needs more validation ({last_score}/100): {last_result.get('summary', '')}"
            partial["partial"] = True
            partial["critique_reason"] = reason
            await _commit(store, workspace_id, task, partial, last_score)
            await store.mark_task_done(task.task_id, last_score)
            await feed.publish(
                workspace_id,
                {"text": f"[Researcher {name}] Committed partial {task.type} research at {last_score}/100; user review needed.", "type": "done", "node_id": task.node_id},
            )
            return
        task.status = "failed"
        task.last_error = reason
        await store.log_dead_end(workspace_id, task.task, reason)
        await _mark_failure(workspace_id, store, task, reason, last_result, last_score)
        await feed.publish(workspace_id, {"text": f"[Researcher {name}] Dead end: {reason}", "type": "error", "node_id": task.node_id})
        return


async def execute_tools(query: str, tools: list[str]) -> list[dict[str, Any]]:
    selected = tools or ["firecrawl", "reddit"]
    calls: list[tuple[str, Any]] = []
    for tool in selected:
        tool = str(tool).lower().strip()
        if tool == "reddit":
            calls.append((tool, reddit_praw.search(query, limit=5)))
        elif tool == "firecrawl":
            calls.append((tool, firecrawl.search(query, limit=5)))
        elif tool in {"scrapling", "web"}:
            calls.append(("scrapling", scrapling_web.search_broad(query, limit=5)))
        elif tool == "github":
            calls.append((tool, github_search.search_repositories(query, limit=5)))
        elif tool in {"exa", "gummysearch"}:
            calls.append(("scrapling", scrapling_web.search_broad(query, limit=5)))
        elif tool in {"producthunt", "product_hunt"}:
            calls.append(("firecrawl", firecrawl.search(query, limit=5)))
    if not calls:
        calls = [("firecrawl", firecrawl.search(query, limit=5)), ("reddit", reddit_praw.search(query, limit=5))]

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
    summary = _clean_summary(summary, task, items)
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


async def _mark_progress(workspace_id: str, store: GraphStore, task: ResearchTask, name: str, note: str) -> None:
    node = await _get_task_node(workspace_id, store, task)
    if node is None:
        return
    updated = node.model_copy(deep=True)
    try:
        agent_id = node_agent_id(NodeType(task.type))
    except ValueError:
        agent_id = node_agent_id(updated.type)
    updated.active_agents = [agent_id]
    updated.agent_notes = note
    updated.summary = note[:240]
    updated.research_history.append(
        {
            "task_id": task.task_id,
            "task": task.task,
            "status": "running",
            "attempt": max(1, task.attempts),
            "query": task.query or task.task,
            "tools": task.tools,
        }
    )
    await store.update_node(workspace_id, updated)


async def _mark_failure(
    workspace_id: str,
    store: GraphStore,
    task: ResearchTask,
    reason: str,
    result: dict[str, Any] | None = None,
    score: int = 0,
) -> None:
    node = await _get_task_node(workspace_id, store, task)
    if node is None:
        return
    updated = node.model_copy(deep=True)
    updated.active_agents = []
    updated.status = NodeStatus.BLOCKING
    updated.agent_notes = f"Research attempted but not accepted: {reason}"
    updated.summary = updated.agent_notes[:240]
    updated.research_history.append(
        {
            "task_id": task.task_id,
            "task": task.task,
            "status": "failed",
            "score": score,
            "reason": reason,
            "result": result or {},
        }
    )
    await store.update_node(workspace_id, updated)


async def _get_task_node(workspace_id: str, store: GraphStore, task: ResearchTask) -> BaseNode | None:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        return None
    existing = next((node for node in workspace.nodes if node.node_id == task.node_id or node.type.value == task.type), None)
    if existing is not None:
        return existing
    data: dict[str, Any] = {
        "type": task.type,
        "title": task.type.replace("_", " ").title(),
        "summary": "Research queued.",
        "unlock_conditions": UnlockConditions(),
    }
    if task.node_id:
        data["node_id"] = task.node_id
    return BaseNode(**data)


def _should_commit_partial(result: dict[str, Any], score: int) -> bool:
    return 75 <= score < 80 and bool(result.get("items")) and bool(result.get("sources"))


def _clean_summary(summary: str, task: ResearchTask, items: list[dict[str, Any]]) -> str:
    text = str(summary or "").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text or _fallback_summary(task, items)
    if isinstance(parsed, dict) and {"score", "verdict"}.intersection(parsed):
        return _fallback_summary(task, items)
    return text or _fallback_summary(task, items)


def _fallback_summary(task: ResearchTask, items: list[dict[str, Any]]) -> str:
    titles = "; ".join(str(i.get("title") or i.get("snippet") or "evidence") for i in items[:3])
    return f"Research for {task.type}: {titles or 'no high-quality evidence found yet.'}"
