from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.graph.schema import WorkspaceCreateRequest, WorkspaceDocument
from backend.graph.node_manager import NodeManager # Import NodeManager

router = APIRouter(tags=["workspace"])

# Instantiate NodeManager globally for use in API endpoints
node_manager = NodeManager()

class WorkspaceResponse(BaseModel):
    idea_id: str
    workspace_name: str
    nodes: list


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
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )
