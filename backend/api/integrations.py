"""GitHub + PostHog integration routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agents.build_observer import observe_build
from agents.observe_agent import observe_funnel
from agents.store_protocol import DEFAULT_STORE

router = APIRouter(tags=["integrations"])

_INTEGRATION_STATE: dict[str, dict[str, object]] = {}


class GitHubConnectRequest(BaseModel):
    workspace_id: str
    repo: str
    access_token: str | None = None


class PostHogConnectRequest(BaseModel):
    workspace_id: str
    project_id: str
    api_key: str


def _state(workspace_id: str) -> dict[str, object]:
    return _INTEGRATION_STATE.setdefault(workspace_id, {})


@router.get("/integrations")
async def get_integrations(workspace_id: str = Query(...)):
    workspace = await DEFAULT_STORE.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    state = _state(workspace_id)
    return {
        "github": bool(state.get("github_connected")),
        "posthog": bool(state.get("posthog_connected")),
        "reddit": True,
        "gummysearch": bool(state.get("gummysearch_connected", False)),
    }


@router.post("/integrations/github")
async def connect_github(payload: GitHubConnectRequest):
    workspace = await DEFAULT_STORE.get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        await observe_build(payload.workspace_id, payload.repo, store=DEFAULT_STORE, token=payload.access_token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    state = _state(payload.workspace_id)
    state["github_connected"] = True
    state["github_repo"] = payload.repo
    return {"connected": True, "build_node_unlocked": True}


@router.post("/integrations/posthog")
async def connect_posthog(payload: PostHogConnectRequest):
    workspace = await DEFAULT_STORE.get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        await observe_funnel(payload.workspace_id, store=DEFAULT_STORE, project_id=payload.project_id, api_key=payload.api_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    state = _state(payload.workspace_id)
    state["posthog_connected"] = True
    state["posthog_project_id"] = payload.project_id
    return {"connected": True, "observe_node_unlocked": True}
