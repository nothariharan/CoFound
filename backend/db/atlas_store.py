"""Atlas-backed GraphStore implementation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from agents.store_protocol import ResearchTask, _coerce_node_type, _infer_task_type, _merge_source_pills, _source_pills, publish_workspace_update
from db import collections as col
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


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AtlasGraphStore:
    """Production GraphStore backed by MongoDB Atlas."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.workspaces = db[col.STARTUP_GRAPHS]
        self.task_queue = db[col.TASK_QUEUE]
        self.dead_ends = db[col.DEAD_ENDS]
        self.journal = db[col.DECISION_JOURNAL]
        self.knowledge_base = db[col.PRODUCT_KNOWLEDGE_BASE]
        self.build_events = db[col.BUILD_EVENTS]
        self.observe_events = db[col.OBSERVE_EVENTS]

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        doc = await self.workspaces.find_one({"idea_id": idea_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        workspace = WorkspaceDocument.model_validate(doc)
        workspace.nodes = compute_unlock_states(workspace.nodes)
        return workspace

    async def save_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        workspace.last_active = _now_utc()
        payload = workspace.model_dump(mode="json")
        await self.workspaces.update_one({"idea_id": workspace.idea_id}, {"$set": payload}, upsert=True)
        return workspace

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        workspace = await self.get_workspace(idea_id)
        if workspace is None:
            raise KeyError(f"Workspace not found: {idea_id}")

        before = next((n for n in workspace.nodes if n.node_id == node.node_id or n.type == node.type), None)
        confidence_before = before.confidence if before else 0
        node.last_updated = _now_utc()

        replaced = False
        for i, existing in enumerate(workspace.nodes):
            if existing.node_id == node.node_id or existing.type == node.type:
                workspace.nodes[i] = node
                replaced = True
                break
        if not replaced:
            workspace.nodes.append(node)

        if before is not None and before.confidence != node.confidence:
            snapshots = list(node.historical_snapshots)
            snapshots.append(create_snapshot(node.confidence, f"{confidence_before}% -> {node.confidence}%"))
            node.historical_snapshots = snapshots

        workspace.nodes = compute_unlock_states(workspace.nodes)
        await self.save_workspace(workspace)
        await publish_workspace_update(idea_id, workspace)

        if before is None or before.confidence != node.confidence or before.status != node.status:
            await self._append_journal(
                idea_id=idea_id,
                node_type=node.type.value,
                event="confidence_updated" if before and before.confidence != node.confidence else "node_updated",
                reason=f"Node {node.type.value} updated",
                evidence=node.sources[:5],
                confidence_before=confidence_before,
                confidence_after=node.confidence,
            )
        return node

    async def enqueue_task(self, task: ResearchTask) -> None:
        payload = task.model_dump(mode="json")
        payload["created_at"] = _now_utc().isoformat()
        existing = await self.task_queue.find_one({"task_id": task.task_id})
        if existing is None:
            await self.task_queue.insert_one(payload)

    async def pop_pending_task(self, workspace_id: str) -> ResearchTask | None:
        doc = await self.task_queue.find_one_and_update(
            {"workspace_id": workspace_id, "status": "pending"},
            {"$set": {"status": "running"}, "$inc": {"attempts": 1}},
            sort=[("priority", 1)],
        )
        if doc is None:
            return None
        doc.pop("_id", None)
        return ResearchTask.model_validate(doc)

    async def requeue_task(self, task: ResearchTask, reason: str | None = None) -> None:
        task.status = "pending"
        task.last_error = reason
        await self.enqueue_task(task)

    async def mark_task_done(self, task_id: str, score: int) -> None:
        await self.task_queue.update_one(
            {"task_id": task_id},
            {"$set": {"status": "done", "score": score, "done_at": _now_utc().isoformat()}},
        )

    async def log_dead_end(self, workspace_id: str, task: str, reason: str) -> None:
        node_type = _coerce_node_type(_infer_task_type(task))
        timestamp = _now_utc().isoformat()
        await self.dead_ends.insert_one(
            {
                "workspace_id": workspace_id,
                "task": task,
                "reason": reason,
                "timestamp": timestamp,
            }
        )
        await self._append_journal(
            idea_id=workspace_id,
            node_type=node_type.value,
            event="research_dead_end",
            reason=reason,
            evidence=[],
            confidence_before=0,
            confidence_after=0,
        )

    async def search_knowledge_base(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        try:
            pipeline = [
                {
                    "$search": {
                        "index": "product_knowledge_base_vector_index",
                        "text": {"query": query, "path": ["title", "snippet", "content"]},
                    }
                },
                {"$limit": limit},
                {"$project": {"title": 1, "snippet": 1, "content": 1, "score": {"$meta": "searchScore"}}},
            ]
            cursor = self.knowledge_base.aggregate(pipeline)
            results = []
            async for doc in cursor:
                results.append(
                    {
                        "title": doc.get("title", "Knowledge"),
                        "snippet": doc.get("snippet") or (doc.get("content") or "")[:240],
                    }
                )
            if results:
                return results
        except Exception:
            pass

        cursor = self.knowledge_base.find(
            {"$or": [{"title": {"$regex": query[:80], "$options": "i"}}, {"snippet": {"$regex": query[:80], "$options": "i"}}]},
            {"title": 1, "snippet": 1},
        ).limit(limit)
        results = []
        async for doc in cursor:
            results.append({"title": doc.get("title", "Knowledge"), "snippet": doc.get("snippet", "")})
        if results:
            return results

        return [
            {"title": "PMF heuristic", "snippet": "Prefer tasks that validate painful, frequent, budgeted problems."},
            {"title": "Competitor heuristic", "snippet": "List direct, indirect, and do-nothing alternatives."},
            {"title": "Pricing heuristic", "snippet": "Look for existing spend, urgency, and willingness to switch."},
        ][:limit]

    async def commit_research_result(
        self,
        workspace_id: str,
        task: ResearchTask,
        result: dict[str, Any],
        score: int,
    ) -> BaseNode:
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
                "status": "partial" if result.get("partial") else "accepted",
                "reason": result.get("critique_reason", ""),
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

    async def log_build_event(self, workspace_id: str, payload: dict[str, Any]) -> None:
        await self.build_events.insert_one(
            {"workspace_id": workspace_id, "timestamp": _now_utc().isoformat(), **payload}
        )

    async def log_observe_event(self, workspace_id: str, payload: dict[str, Any]) -> None:
        await self.observe_events.insert_one(
            {"workspace_id": workspace_id, "timestamp": _now_utc().isoformat(), **payload}
        )

    async def list_journal(self, idea_id: str) -> list[dict[str, Any]]:
        cursor = self.journal.find({"idea_id": idea_id}).sort("timestamp", -1)
        entries: list[dict[str, Any]] = []
        async for doc in cursor:
            doc.pop("_id", None)
            entries.append(doc)
        return entries

    async def _append_journal(
        self,
        *,
        idea_id: str,
        node_type: str,
        event: str,
        reason: str,
        evidence: list[str],
        confidence_before: int,
        confidence_after: int,
    ) -> None:
        await self.journal.insert_one(
            {
                "entry_id": str(uuid4()),
                "idea_id": idea_id,
                "timestamp": _now_utc().isoformat(),
                "node_type": node_type,
                "event": event,
                "reason": reason,
                "evidence": evidence,
                "confidence_before": confidence_before,
                "confidence_after": confidence_after,
            }
        )
