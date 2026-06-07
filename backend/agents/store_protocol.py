"""Track B GraphStore protocol and interim memory implementation.

Agents depend on this protocol instead of MongoDB details.  Track A can swap in an
Atlas-backed implementation with the same methods.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from backend.db.connection import db
from backend.db.collections import DECISION_JOURNAL, TASK_QUEUE, DEAD_ENDS
from backend.graph.schema import (
    BaseNode,
    SourcePill,
    UnlockConditions,
    WorkspaceDocument,
    NodeType, # Import NodeType Enum
)
from backend.graph.node_manager import NodeManager


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
    async def commit_research_result(self, workspace_id: str, task: ResearchTask, result: dict[str, Any], score: int) -> BaseNode: ...


class AtlasGraphStore:
    """Atlas-backed GraphStore implementation."""

    def __init__(self) -> None:
        self.node_manager = NodeManager()
        self.task_queue_collection = db.db[TASK_QUEUE]
        self.decision_journal_collection = db.db[DECISION_JOURNAL]
        self.dead_ends_collection = db.db[DEAD_ENDS]

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        try:
            idea_uuid = UUID(idea_id)
        except ValueError:
            return None
        return await self.node_manager.get_workspace(idea_uuid)

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        # Ensure the node's last_updated field is current
        node.last_updated = _now_utc()
        updated_node = await self.node_manager.update_node(node.node_id, node.model_dump(by_alias=True, exclude_unset=True))
        if updated_node:
            return updated_node
        # If update_node returns None, it means the node didn't exist, so create it.
        # This scenario might happen if a node is added to a workspace but not yet persisted
        # as a standalone node in the nodes collection.
        await self.node_manager.create_node(node)
        return node

    async def enqueue_task(self, task: ResearchTask) -> None:
        task_dict = task.model_dump(by_alias=True)
        # Convert UUID to string for MongoDB storage
        task_dict["task_id"] = str(task.task_id)
        task_dict["workspace_id"] = str(task.workspace_id)
        if task.node_id:
            task_dict["node_id"] = str(task.node_id)

        # Check if task already exists to avoid duplicates
        existing_task = await self.task_queue_collection.find_one({"task_id": task_dict["task_id"]})
        if not existing_task:
            await self.task_queue_collection.insert_one(task_dict)

    async def pop_pending_task(self, workspace_id: str) -> ResearchTask | None:
        # Find one pending task for the given workspace_id and update its status to 'running'
        task_dict = await self.task_queue_collection.find_one_and_update(
            {"workspace_id": workspace_id, "status": "pending"},
            {"$set": {"status": "running", "attempts": {"$inc": 1}}},
            return_document=True # Return the updated document
        )
        if task_dict:
            return ResearchTask(**task_dict)
        return None

    async def mark_task_done(self, task_id: str, score: int) -> None:
        await self.task_queue_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "done", "score": score, "done_at": _now_utc().isoformat()}}
        )

    async def log_dead_end(self, workspace_id: str, task: str, reason: str) -> None:
        dead_end_entry = {
            "workspace_id": workspace_id,
            "task": task,
            "reason": reason,
            "timestamp": _now_utc().isoformat(),
        }
        await self.dead_ends_collection.insert_one(dead_end_entry)

    async def search_knowledge_base(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        # This will be implemented in Phase 3. For now, return a mock.
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
        existing_node = next((n for n in workspace.nodes if n.type == node_type), None)

        confidence = max(score, existing_node.confidence if existing_node else 0)
        status = _status_from_confidence(confidence)
        sources = sorted(set((existing_node.sources if existing_node else []) + list(result.get("sources", []))))
        source_pills = _merge_source_pills(existing_node.source_pills if existing_node else [], _source_pills(result))
        notes = result.get("summary") or result.get("answer") or result.get("notes") or "Research committed."

        node_id = existing_node.node_id if existing_node else _canonical_node_id(node_type)

        node = BaseNode(
            node_id=node_id,
            type=node_type,
            confidence=confidence,
            status=status,
            sources=sources,
            source_pills=source_pills,
            agent_notes=notes,
            title=(existing_node.title if existing_node and existing_node.title else node_type.value.replace("_", " ").title()),
            summary=str(notes)[:240],
            unlock_conditions=existing_node.unlock_conditions if existing_node else UnlockConditions(),
            # chat_history and research_history are not part of BaseNode schema
            # historical_snapshots is part of BaseNode schema but not updated here
        )
        
        # Update or create the node in the database
        updated_node = await self.node_manager.update_node(node.node_id, node.model_dump(by_alias=True, exclude_unset=True))
        if not updated_node:
            # If update failed (node didn't exist in nodes collection), create it
            await self.node_manager.create_node(node)
            updated_node = node
            # Also add the node reference to the workspace document if it's new
            await self.node_manager.add_node_to_workspace(UUID(workspace_id), node)

        return updated_node


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _status_from_confidence(confidence: int) -> Literal["validated", "needs_work", "blocking", "locked"]:
    if confidence >= 70:
        return "validated"
    elif confidence > 0:
        return "needs_work"
    return "locked" # Default to locked if 0 confidence or less

def _canonical_node_id(node_type: NodeType) -> UUID:
    # This is a placeholder. In a real system, you might generate a stable UUID
    # based on the node_type or use a predefined one.
    # For now, we'll just generate a new UUID.
    return uuid4()

def _coerce_node_type(value: str) -> NodeType:
    value = (value or "market_intelligence").lower().strip()
    aliases = {"market": "market_intelligence", "persona": "audience", "customers": "audience"}
    value = aliases.get(value, value)
    try:
        return NodeType(value)
    except ValueError:
        # Handle cases where the string value might not directly map to an Enum member
        # For example, if the string is "market_intelligence" but the Enum member is MARKET_INTELLIGENCE
        for node_type_enum in NodeType:
            if node_type_enum.value == value:
                return node_type_enum
        # If still not found, raise an error or return a default
        raise ValueError(f"Invalid NodeType value: {value}")


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


# Update DEFAULT_STORE to use AtlasGraphStore
DEFAULT_STORE = AtlasGraphStore()
