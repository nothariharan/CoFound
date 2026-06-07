from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from backend.db.connection import db
from backend.db.collections import Collection
from backend.graph.schema import WorkspaceCreateRequest, WorkspaceDocument
from backend.graph.node_manager import NodeManager
from backend.graph.unlock_engine import compute_unlock_states

router = APIRouter(tags=["workspace"])

# Instantiate NodeManager globally for use in API endpoints
node_manager = NodeManager()

class WorkspaceResponse(BaseModel):
    idea_id: str
    workspace_name: str
    nodes: list

class JournalEntryResponse(BaseModel):
    timestamp: str
    node_id: str
    update_data: dict

@router.post("/workspace", response_model=WorkspaceResponse)
async def create_workspace(body: WorkspaceCreateRequest):
    """
    Creates a new workspace with an initial Core Idea node, persisting it to MongoDB Atlas.
    """
    workspace = await node_manager.create_workspace_with_core_idea(body.idea)
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )


@router.get("/workspace/{idea_id}", response_model=WorkspaceResponse)
async def get_workspace(idea_id: str):
    """
    Retrieves a workspace by its ID from MongoDB Atlas.
    """
    workspace = await node_manager.get_workspace(idea_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Apply unlock logic
    workspace.nodes = compute_unlock_states(workspace.nodes)

    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )

@router.get("/workspace/{workspace_id}/journal", response_model=List[JournalEntryResponse])
async def get_workspace_journal(workspace_id: str):
    """
    Retrieves the decision journal entries for a given workspace.
    """
    workspace = await node_manager.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    node_ids = [node.id for node in workspace.nodes]

    journal_entries_cursor = db.database[Collection.DECISION_JOURNAL].find(
        {"node_id": {"$in": node_ids}}
    ).sort("timestamp", 1) # Sort by timestamp ascending

    journal_entries = []
    async for entry in journal_entries_cursor:
        journal_entries.append(JournalEntryResponse(
            timestamp=entry["timestamp"].isoformat(), # Convert datetime to ISO format string
            node_id=entry["node_id"],
            update_data=entry["update_data"]
        ))
    return journal_entries
