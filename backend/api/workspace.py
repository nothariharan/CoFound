from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import UUID

from backend.db.connection import db
from backend.db.collections import DECISION_JOURNAL # Corrected import
from backend.graph.schema import WorkspaceCreateRequest, WorkspaceDocument, BaseNode
from backend.graph.node_manager import NodeManager
from backend.graph.unlock_engine import compute_unlock_states

router = APIRouter(tags=["workspace"])

# Instantiate NodeManager globally for use in API endpoints
node_manager = NodeManager()

class WorkspaceResponse(BaseModel):
    idea_id: UUID
    workspace_name: str
    nodes: List[BaseNode] # Use BaseNode for nodes

class JournalEntry(BaseModel):
    timestamp: str
    node_type: str
    event: str
    reason: str
    evidence: List[str]
    confidence_before: int
    confidence_after: int

class JournalResponse(BaseModel):
    entries: List[JournalEntry]

@router.post("/workspace", response_model=WorkspaceResponse)
async def create_workspace(body: WorkspaceCreateRequest):
    """
    Creates a new workspace with an initial Core Idea node, persisting it to MongoDB Atlas.
    """
    workspace = await node_manager.create_workspace_with_core_idea(body.idea)
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=workspace.nodes, # Pass BaseNode objects directly
    )


@router.get("/workspace/{idea_id}", response_model=WorkspaceResponse)
async def get_workspace(idea_id: str):
    """
    Retrieves a workspace by its ID from MongoDB Atlas.
    """
    try:
        idea_uuid = UUID(idea_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid idea_id format")

    workspace = await node_manager.get_workspace(idea_uuid)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Apply unlock logic
    workspace.nodes = compute_unlock_states(workspace.nodes)

    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=workspace.nodes, # Pass BaseNode objects directly
    )

@router.get("/workspace/{workspace_id}/journal", response_model=JournalResponse)
async def get_workspace_journal(workspace_id: str):
    """
    Retrieves the decision journal entries for a given workspace.
    """
    try:
        workspace_uuid = UUID(workspace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workspace_id format")

    workspace = await node_manager.get_workspace(workspace_uuid)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    node_ids = [str(node.node_id) for node in workspace.nodes] # Corrected node.id to node.node_id and converted to string

    journal_entries_cursor = db.db[DECISION_JOURNAL].find( # Corrected collection access
        {"node_id": {"$in": node_ids}}
    ).sort("timestamp", 1) # Sort by timestamp ascending

    journal_entries = []
    async for entry in journal_entries_cursor:
        journal_entries.append(JournalEntry(
            timestamp=entry["timestamp"].isoformat(), # Convert datetime to ISO format string
            node_type=entry["node_type"],
            event=entry["event"],
            reason=entry["reason"],
            evidence=entry.get("evidence", []), # Use .get for optional fields
            confidence_before=entry["confidence_before"],
            confidence_after=entry["confidence_after"]
        ))
    return JournalResponse(entries=journal_entries)
