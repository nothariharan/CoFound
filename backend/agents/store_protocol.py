"""Track B GraphStore protocol and interim memory implementation.

Agents depend on this protocol instead of MongoDB details.  Track A can swap in an
Atlas-backed implementation with the same methods.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from graph.schema import BaseNode, NodeType, SourcePill, UnlockConditions, WorkspaceDocument, status_from_confidence


class ResearchTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    type: str
    tools: list[str] = Field(default_factory=list)
    priority: int = 5
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3
    workspace_id: str
    node_id: str | None = None
    query: str | None = None
    last_error: str | None = None


class GraphStore(Protocol):
    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None: ...
    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode: ...
    async def enqueue_task(self, task: ResearchTask) -> None: ...
    async def pop_pending_task(self, workspace_id: str) -> ResearchTask | None: ...
    async def mark_task_done(self, task_id: str, score: int) -> None: ...
    async def log_dead_end(self, workspace_id: str, task: str, reason: str) -> None: ...
    async def search_knowledge_base(self, query: str, limit: int = 5) -> list[dict[str, Any]]: ...


class MemoryGraphStore:
    """Small interim GraphStore backed by the repo's current in-memory dict."""

    def __init__(self) -> None:
        # Track A owns backend/store.py. This adapter only wraps it until Atlas lands.
        from store import WORKSPACES  # type: ignore

        self.workspaces: dict[str, WorkspaceDocument] = WORKSPACES
        self.task_queue: list[ResearchTask] = []
        self.dead_ends: list[dict[str, Any]] = []
        self.task_results: dict[str, dict[str, Any]] = {}
        self.priority_cache: dict[str, dict[str, Any]] = {}

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        return self.workspaces.get(idea_id)

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        workspace = self.workspaces.get(idea_id)
        if workspace is None:
            raise KeyError(f"Workspace not found: {idea_id}")
        node.last_updated = _now_utc()
        for i, existing in enumerate(workspace.nodes):
            if existing.node_id == node.node_id or existing.type == node.type:
                workspace.nodes[i] = node
                workspace.last_active = _now_utc()
                return node
        workspace.nodes.append(node)
        workspace.last_active = _now_utc()
        return node

    async def enqueue_task(self, task: ResearchTask) -> None:
        if not any(t.task_id == task.task_id for t in self.task_queue):
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority)

    async def pop_pending_task(self, workspace_id: str) -> ResearchTask | None:
        for task in self.task_queue:
            if task.workspace_id == workspace_id and task.status == "pending":
                task.status = "running"
                task.attempts += 1
                return task
        return None

    async def requeue_task(self, task: ResearchTask, reason: str | None = None) -> None:
        task.status = "pending"
        task.last_error = reason
        await self.enqueue_task(task)

    async def mark_task_done(self, task_id: str, score: int) -> None:
        for task in self.task_queue:
            if task.task_id == task_id:
                task.status = "done"
                self.task_results[task_id] = {"score": score, "done_at": _now_utc().isoformat()}
                return

    async def log_dead_end(self, workspace_id: str, task: str, reason: str) -> None:
        self.dead_ends.append(
            {
                "workspace_id": workspace_id,
                "task": task,
                "reason": reason,
                "timestamp": _now_utc().isoformat(),
            }
        )

    async def search_knowledge_base(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        # Mock KB until Track A vector search lands. Keep deterministic and useful.
        return [
            {"title": "PMF heuristic", "snippet": "Prefer tasks that validate painful, frequent, budgeted problems."},
            {"title": "Competitor heuristic", "snippet": "List direct, indirect, and do-nothing alternatives."},
            {"title": "Pricing heuristic", "snippet": "Look for existing spend, urgency, and willingness to switch."},
        ][:limit]

    async def commit_research_result(self, workspace_id: str, task: ResearchTask, result: dict[str, Any], score: int) -> BaseNode:
        workspace = await self.get_workspace(workspace_id)
        if workspace is None:
            raise KeyError(f"Workspace not found: {workspace_id}")

        node_type = _coerce_node_type(task.type)
        existing = next((n for n in workspace.nodes if n.type == node_type), None)
        confidence = max(score, existing.confidence if existing else 0)
        status = status_from_confidence(confidence)
        sources = sorted(set((existing.sources if existing else []) + list(result.get("sources", []))))
        source_pills = _merge_source_pills(existing.source_pills if existing else [], _source_pills(result))
        notes = result.get("summary") or result.get("answer") or result.get("notes") or "Research committed."
        history = list(existing.research_history if existing else [])
        history.append(
            {
                "task_id": task.task_id,
                "task": task.task,
                "score": score,
                "result": result,
                "timestamp": _now_utc().isoformat(),
            }
        )
        node = BaseNode(
            node_id=existing.node_id if existing else str(uuid4()),
            type=node_type,
            confidence=confidence,
            status=status,
            sources=sources,
            source_pills=source_pills,
            agent_notes=notes,
            chat_history=existing.chat_history if existing else [],
            research_history=history,
            active_agents=[],
            title=(existing.title if existing and existing.title else node_type.value.replace("_", " ").title()),
            summary=str(notes)[:240],
            unlock_conditions=existing.unlock_conditions if existing else UnlockConditions(),
            historical_snapshots=existing.historical_snapshots if existing else [],
        )
        return await self.update_node(workspace_id, node)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_node_type(value: str) -> NodeType:
    value = (value or "market_intelligence").lower().strip()
    aliases = {"market": "market_intelligence", "persona": "audience", "customers": "audience"}
    value = aliases.get(value, value)
    try:
        return NodeType(value)
    except ValueError:
        return NodeType.MARKET_INTELLIGENCE


def _source_pills(result: dict[str, Any]) -> list[SourcePill]:
    counts: dict[str, int] = {}
    for item in result.get("items", []) or []:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or item.get("tool") or "Research").title()
        counts[source] = counts.get(source, 0) + 1
    return [SourcePill(label=label, count=count) for label, count in counts.items()]


def _merge_source_pills(existing: list[SourcePill], new: list[SourcePill]) -> list[SourcePill]:
    merged: dict[str, SourcePill] = {pill.label: pill.model_copy() for pill in existing}
    for pill in new:
        if pill.label in merged:
            merged[pill.label].count += pill.count
            merged[pill.label].url = merged[pill.label].url or pill.url
        else:
            merged[pill.label] = pill
    return list(merged.values())


DEFAULT_STORE = MemoryGraphStore()
