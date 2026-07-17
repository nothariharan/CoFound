"""github + posthog integration routes"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agents.build_observer import observe_build
from agents.observe_agent import observe_funnel
from agents.store_protocol import DEFAULT_STORE, get_store, publish_workspace_update

router = APIRouter(tags=["integrations"])

class GitHubConnectRequest(BaseModel):
    workspace_id: str
    repo: str
    access_token: str | None = None


class PostHogConnectRequest(BaseModel):
    workspace_id: str
    project_id: str
    api_key: str


@router.get("/integrations")
async def get_integrations(workspace_id: str = Query(...)):
    workspace = await DEFAULT_STORE.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "github": bool(workspace.github_connected),
        "posthog": bool(workspace.posthog_connected),
        "reddit": True,
    }


@router.post("/integrations/github")
async def connect_github(payload: GitHubConnectRequest):
    workspace = await DEFAULT_STORE.get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        await observe_build(payload.workspace_id, payload.repo, store=get_store(), token=payload.access_token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    workspace.github_connected = True
    workspace.github_repo = payload.repo
    if hasattr(DEFAULT_STORE, "save_workspace"):
        await DEFAULT_STORE.save_workspace(workspace)
    await publish_workspace_update(payload.workspace_id, workspace)
    return {"connected": True, "build_node_unlocked": True}


@router.post("/integrations/posthog")
async def connect_posthog(payload: PostHogConnectRequest):
    workspace = await DEFAULT_STORE.get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        await observe_funnel(payload.workspace_id, store=get_store(), project_id=payload.project_id, api_key=payload.api_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    workspace.posthog_connected = True
    workspace.posthog_project_id = payload.project_id
    if hasattr(DEFAULT_STORE, "save_workspace"):
        await DEFAULT_STORE.save_workspace(workspace)
    await publish_workspace_update(payload.workspace_id, workspace)
    return {"connected": True, "observe_node_unlocked": True}
