"""Track B GraphStore protocol and interim memory implementation.

Agents depend on this protocol instead of MongoDB details.  Track A can swap in an
Atlas-backed implementation with the same methods.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from graph.schema import (
    BaseNode,
    NodeType,
    SourcePill,
    UnlockConditions,
    WorkspaceDocument,
    canonical_node_id,
    status_from_confidence,
)
from graph.snapshot import create_snapshot
from graph.unlock_engine import compute_unlock_states

MEMORY_WORKSPACES: dict[str, WorkspaceDocument] = {}


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
        self.workspaces: dict[str, WorkspaceDocument] = MEMORY_WORKSPACES
        self.task_queue: list[ResearchTask] = []
        self.dead_ends: list[dict[str, Any]] = []
        self.task_results: dict[str, dict[str, Any]] = {}
        self.priority_cache: dict[str, dict[str, Any]] = {}
        self.journal_entries: list[dict[str, Any]] = []
        self.build_events: list[dict[str, Any]] = []
        self.observe_events: list[dict[str, Any]] = []

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        workspace = self.workspaces.get(idea_id)
        if workspace is None:
            return None
        workspace.nodes = compute_unlock_states(workspace.nodes)
        return workspace

    async def save_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        workspace.last_active = _now_utc()
        self.workspaces[workspace.idea_id] = workspace
        return workspace

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        workspace = self.workspaces.get(idea_id)
        if workspace is None:
            raise KeyError(f"Workspace not found: {idea_id}")
        before = next((n for n in workspace.nodes if n.node_id == node.node_id or n.type == node.type), None)
        confidence_before = before.confidence if before else 0
        node.last_updated = _now_utc()
        if before is not None and before.confidence != node.confidence:
            snapshots = list(node.historical_snapshots)
            snapshots.append(create_snapshot(node.confidence, f"{confidence_before}% -> {node.confidence}%"))
            node.historical_snapshots = snapshots
        for i, existing in enumerate(workspace.nodes):
            if existing.node_id == node.node_id or existing.type == node.type:
                workspace.nodes[i] = node
                workspace.last_active = _now_utc()
                if before is None or before.confidence != node.confidence or before.status != node.status:
                    await self._append_journal(idea_id, node, confidence_before, before)
                return node
        workspace.nodes.append(node)
        workspace.last_active = _now_utc()
        await self._append_journal(idea_id, node, confidence_before, before)
        return node

    async def _append_journal(self, idea_id: str, node: BaseNode, confidence_before: int, before: BaseNode | None) -> None:
        self.journal_entries.append(
            {
                "entry_id": str(uuid4()),
                "idea_id": idea_id,
                "timestamp": _now_utc().isoformat(),
                "node_type": node.type.value,
                "event": "confidence_updated" if before and before.confidence != node.confidence else "node_updated",
                "reason": f"Node {node.type.value} updated",
                "evidence": node.sources[:5],
                "confidence_before": confidence_before,
                "confidence_after": node.confidence,
            }
        )

    async def list_journal(self, idea_id: str) -> list[dict[str, Any]]:
        return [e for e in self.journal_entries if e.get("idea_id") == idea_id]

    async def log_build_event(self, workspace_id: str, payload: dict[str, Any]) -> None:
        self.build_events.append({"workspace_id": workspace_id, "timestamp": _now_utc().isoformat(), **payload})

    async def log_observe_event(self, workspace_id: str, payload: dict[str, Any]) -> None:
        self.observe_events.append({"workspace_id": workspace_id, "timestamp": _now_utc().isoformat(), **payload})

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
            node_id=existing.node_id if existing else canonical_node_id(node_type),
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


class StoreProxy:
    """Mutable proxy so lifespan can swap MemoryGraphStore for AtlasGraphStore."""

    def __init__(self) -> None:
        self._store: GraphStore = MemoryGraphStore()

    def set(self, store: GraphStore) -> None:
        self._store = store

    def get(self) -> GraphStore:
        return self._store

    def __getattr__(self, name: str):
        return getattr(self._store, name)


DEFAULT_STORE: StoreProxy = StoreProxy()
