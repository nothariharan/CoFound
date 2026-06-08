from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.store_protocol import DEFAULT_STORE
from graph.node_manager import NodeManager
from graph.schema import WorkspaceCreateRequest, WorkspaceDocument, create_core_idea_node
from graph.unlock_engine import compute_unlock_states

router = APIRouter(tags=["workspace"])
_node_manager = NodeManager()


class WorkspaceResponse(BaseModel):
    idea_id: str
    workspace_name: str
    nodes: list


class JournalResponse(BaseModel):
    entries: list


def _to_response(workspace: WorkspaceDocument) -> WorkspaceResponse:
    workspace.nodes = compute_unlock_states(workspace.nodes)
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )


@router.post("/workspace", response_model=WorkspaceResponse)
async def create_workspace(body: WorkspaceCreateRequest):
    idea_id = str(uuid4())
    core_node = create_core_idea_node(body.idea)
    workspace = WorkspaceDocument(
        idea_id=idea_id,
        workspace_name=body.idea.strip()[:60] or "Untitled Startup",
        nodes=[core_node],
    )
    await DEFAULT_STORE.save_workspace(workspace)
    return _to_response(workspace)


@router.get("/workspace/{idea_id}", response_model=WorkspaceResponse)
async def get_workspace(idea_id: str):
    workspace = await DEFAULT_STORE.get_workspace(idea_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return _to_response(workspace)


@router.get("/workspace/{idea_id}/journal", response_model=JournalResponse)
async def get_workspace_journal(idea_id: str):
    workspace = await DEFAULT_STORE.get_workspace(idea_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if hasattr(DEFAULT_STORE, "list_journal"):
        entries = await DEFAULT_STORE.list_journal(idea_id)
        return JournalResponse(entries=entries)
    return JournalResponse(entries=[])
