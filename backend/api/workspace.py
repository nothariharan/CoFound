from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph.schema import WorkspaceCreateRequest, WorkspaceDocument, create_core_idea_node
from store import WORKSPACES

router = APIRouter(tags=["workspace"])


class WorkspaceResponse(BaseModel):
    idea_id: str
    workspace_name: str
    nodes: list


@router.post("/workspace", response_model=WorkspaceResponse)
async def create_workspace(body: WorkspaceCreateRequest):
    idea_id = str(uuid4())
    core_node = create_core_idea_node(body.idea)
    workspace = WorkspaceDocument(
        idea_id=idea_id,
        workspace_name=body.idea.strip()[:60] or "Untitled Startup",
        nodes=[core_node],
    )
    WORKSPACES[idea_id] = workspace
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )


@router.get("/workspace/{idea_id}", response_model=WorkspaceResponse)
async def get_workspace(idea_id: str):
    workspace = WORKSPACES.get(idea_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )
