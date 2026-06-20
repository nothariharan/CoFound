"""agent facing graphstore backed by mongodb mcp server tools"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agents.store_protocol import ResearchTask, _coerce_node_type, _find_existing_node, _infer_task_type, _merge_source_pills, _node_update_matches, _source_pills, publish_workspace_update
from db import collections as col
from graph.schema import BaseNode, UnlockConditions, WorkspaceDocument, canonical_node_id, status_from_confidence
from graph.snapshot import create_snapshot
from graph.unlock_engine import compute_unlock_states
from mdb_mcp import db_ops


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class McpGraphStore:
    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        doc = await db_ops.mcp_find_one(col.STARTUP_GRAPHS, filter={"idea_id": idea_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        workspace = WorkspaceDocument.model_validate(doc)
        workspace.nodes = compute_unlock_states(workspace.nodes)
        return workspace

    async def save_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        workspace.last_active = _now_utc()
        await db_ops.mcp_replace_workspace(workspace.model_dump(mode="json"))
        return workspace

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        workspace = await self.get_workspace(idea_id)
        if workspace is None:
            raise KeyError(f"Workspace not found: {idea_id}")

        before = next((n for n in workspace.nodes if _node_update_matches(n, node)), None)
        confidence_before = before.confidence if before else 0
        node.last_updated = _now_utc()

        replaced = False
        for i, existing in enumerate(workspace.nodes):
            if _node_update_matches(existing, node):
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
        existing = await db_ops.mcp_find_one(col.TASK_QUEUE, filter={"task_id": task.task_id})
        if existing is not None:
            return
        payload = task.model_dump(mode="json")
        payload["created_at"] = _now_utc().isoformat()
        await db_ops.mcp_insert_one(col.TASK_QUEUE, payload)

    async def pop_pending_task(self, workspace_id: str) -> ResearchTask | None:
        doc = await db_ops.mcp_find_one(
            col.TASK_QUEUE,
            filter={"workspace_id": workspace_id, "status": "pending"},
            sort={"priority": 1},
        )
        if doc is None:
            return None
        task_id = doc.get("task_id")
        if not task_id:
            return None
        attempts = int(doc.get("attempts", 0)) + 1
        await db_ops.mcp_update_many(
            col.TASK_QUEUE,
            filter={"task_id": task_id},
            update={"$set": {"status": "running", "attempts": attempts}},
        )
        doc["status"] = "running"
        doc["attempts"] = attempts
        doc.pop("_id", None)
        return ResearchTask.model_validate(doc)

    async def requeue_task(self, task: ResearchTask, reason: str | None = None) -> None:
        task.status = "pending"
        task.last_error = reason
        await self.enqueue_task(task)

    async def mark_task_done(self, task_id: str, score: int) -> None:
        await db_ops.mcp_update_many(
            col.TASK_QUEUE,
            filter={"task_id": task_id},
            update={"$set": {"status": "done", "score": score, "done_at": _now_utc().isoformat()}},
        )

    async def log_dead_end(self, workspace_id: str, task: str, reason: str) -> None:
        node_type = _coerce_node_type(_infer_task_type(task))
        await db_ops.mcp_insert_one(
            col.DEAD_ENDS,
            {"workspace_id": workspace_id, "task": task, "reason": reason, "timestamp": _now_utc().isoformat()},
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
                {"$search": {"index": "product_knowledge_base_vector_index", "text": {"query": query, "path": ["title", "snippet", "content"]}}},
                {"$limit": limit},
                {"$project": {"title": 1, "snippet": 1, "content": 1, "score": {"$meta": "searchScore"}}},
            ]
            docs = await db_ops.mcp_aggregate(col.PRODUCT_KNOWLEDGE_BASE, pipeline)
            results = [{"title": doc.get("title", "Knowledge"), "snippet": doc.get("snippet") or (doc.get("content") or "")[:240]} for doc in docs]
            if results:
                return results
        except Exception:
            pass

        docs = await db_ops.mcp_find(
            col.PRODUCT_KNOWLEDGE_BASE,
            filter={"$or": [{"title": {"$regex": query[:80], "$options": "i"}}, {"snippet": {"$regex": query[:80], "$options": "i"}}]},
            limit=limit,
        )
        if docs:
            return [{"title": doc.get("title", "Knowledge"), "snippet": doc.get("snippet", "")} for doc in docs]

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
        existing = _find_existing_node(workspace, task)
        confidence = max(score, existing.confidence if existing else 0)
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
            node_id=existing.node_id if existing else (task.node_id or canonical_node_id(node_type)),
            type=existing.type if existing else node_type,
            confidence=confidence,
            status=status_from_confidence(confidence),
            sources=sorted(set((existing.sources if existing else []) + list(result.get("sources", [])))),
            source_pills=_merge_source_pills(existing.source_pills if existing else [], _source_pills(result)),
            agent_notes=notes,
            chat_history=existing.chat_history if existing else [],
            research_history=history,
            active_agents=[],
            title=(existing.title if existing and existing.title else node_type.value.replace("_", " ").title()),
            summary=str(notes)[:240],
            unlock_conditions=existing.unlock_conditions if existing else UnlockConditions(),
            historical_snapshots=existing.historical_snapshots if existing else [],
            parent_node_id=existing.parent_node_id if existing else None,
        )
        return await self.update_node(workspace_id, node)

    async def log_build_event(self, workspace_id: str, payload: dict[str, Any]) -> None:
        await db_ops.mcp_insert_one(col.BUILD_EVENTS, {"workspace_id": workspace_id, "timestamp": _now_utc().isoformat(), **payload})

    async def log_observe_event(self, workspace_id: str, payload: dict[str, Any]) -> None:
        await db_ops.mcp_insert_one(col.OBSERVE_EVENTS, {"workspace_id": workspace_id, "timestamp": _now_utc().isoformat(), **payload})

    async def list_journal(self, idea_id: str) -> list[dict[str, Any]]:
        docs = await db_ops.mcp_find(col.DECISION_JOURNAL, filter={"idea_id": idea_id}, sort={"timestamp": -1})
        entries = []
        for doc in docs:
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
        await db_ops.mcp_insert_one(
            col.DECISION_JOURNAL,
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
            },
        )
