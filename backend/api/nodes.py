"""Node read/update routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.store_protocol import DEFAULT_STORE
from graph.schema import BaseNode, NodeStatus, SourcePill, status_from_confidence
from graph.unlock_engine import compute_unlock_states

router = APIRouter(tags=["nodes"])


class NodePatchRequest(BaseModel):
    idea_id: str
    confidence: int | None = Field(default=None, ge=0, le=100)
    status: NodeStatus | None = None
    agent_notes: str | None = None
    source_pills: list[SourcePill] | None = None
    sources: list[str] | None = None
    active_agents: list[str] | None = None
    summary: str | None = None
    title: str | None = None


@router.patch("/nodes/{node_id}")
async def patch_node(node_id: str, body: NodePatchRequest):
    workspace = await DEFAULT_STORE.get_workspace(body.idea_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    existing = next((n for n in workspace.nodes if n.node_id == node_id), None)
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    updated = existing.model_copy(deep=True)
    if body.confidence is not None:
        updated.confidence = body.confidence
    if body.status is not None:
        updated.status = body.status
    elif body.confidence is not None:
        updated.status = status_from_confidence(body.confidence, locked=existing.status == NodeStatus.LOCKED)
    if body.agent_notes is not None:
        updated.agent_notes = body.agent_notes
    if body.source_pills is not None:
        updated.source_pills = body.source_pills
    if body.sources is not None:
        updated.sources = body.sources
    if body.active_agents is not None:
        updated.active_agents = body.active_agents
    if body.summary is not None:
        updated.summary = body.summary
    if body.title is not None:
        updated.title = body.title

    result = await DEFAULT_STORE.update_node(body.idea_id, updated)
    refreshed = await DEFAULT_STORE.get_workspace(body.idea_id)
    if refreshed is not None:
        compute_unlock_states(refreshed.nodes)
    return result.model_dump(mode="json")
