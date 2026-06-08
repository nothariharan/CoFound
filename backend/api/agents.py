"""Agent spawn/status routes — Day 3-4."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agents.build_observer import observe_build
from agents.dialogue import synthesize_dialogue
from agents.diff_classifier import classify_pivot
from agents.growth_agent import recommend_priority
from agents.observe_agent import observe_funnel
from agents.orchestrator import spawn_research_session
from agents.store_protocol import DEFAULT_STORE

router = APIRouter(tags=["agents"])


class SpawnRequest(BaseModel):
    workspace_id: str
    trigger: str = "manual"


class SpawnResponse(BaseModel):
    session_id: str
    tasks_queued: int
    agents_active: int


class PivotRequest(BaseModel):
    workspace_id: str
    message: str


class DialogueRequest(BaseModel):
    workspace_id: str
    message: str | None = None


class DialogueResponse(BaseModel):
    brief: str
    question: str


class ObserveBuildRequest(BaseModel):
    workspace_id: str
    repo: str
    access_token: str | None = None


class ObserveFunnelRequest(BaseModel):
    workspace_id: str
    project_id: str | None = None
    api_key: str | None = None


@router.post("/agents/spawn", response_model=SpawnResponse)
async def spawn_agents(payload: SpawnRequest):
    try:
        result = await spawn_research_session(payload.workspace_id, trigger=payload.trigger, store=DEFAULT_STORE)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SpawnResponse(session_id=result.session_id, tasks_queued=result.tasks_queued, agents_active=result.agents_active)


@router.post("/agents/pivot")
async def pivot_agents(payload: PivotRequest):
    try:
        result = await classify_pivot(payload.workspace_id, payload.message, store=DEFAULT_STORE, enqueue=True)
        if result.get("spawn_researcher"):
            await spawn_research_session(payload.workspace_id, trigger="pivot", store=DEFAULT_STORE)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/priority")
async def priority(workspace_id: str = Query(...)):
    try:
        return await recommend_priority(workspace_id, store=DEFAULT_STORE)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/agents/dialogue", response_model=DialogueResponse)
async def get_dialogue(workspace_id: str = Query(...)):
    try:
        result = await synthesize_dialogue(workspace_id, store=DEFAULT_STORE)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DialogueResponse(brief=result["brief"], question=result["question"])


@router.post("/agents/dialogue", response_model=DialogueResponse)
async def post_dialogue(payload: DialogueRequest):
    try:
        result = await synthesize_dialogue(payload.workspace_id, store=DEFAULT_STORE)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if payload.message:
        result["brief"] = f"{result['brief']} User context: {payload.message.strip()}"
    return DialogueResponse(brief=result["brief"], question=result["question"])


@router.post("/agents/observe")
async def observe_build_route(payload: ObserveBuildRequest):
    try:
        result = await observe_build(payload.workspace_id, payload.repo, store=DEFAULT_STORE, token=payload.access_token)
        if hasattr(DEFAULT_STORE, "log_build_event"):
            await DEFAULT_STORE.log_build_event(payload.workspace_id, result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/agents/observe-funnel")
async def observe_funnel_route(payload: ObserveFunnelRequest):
    try:
        result = await observe_funnel(
            payload.workspace_id,
            store=DEFAULT_STORE,
            project_id=payload.project_id,
            api_key=payload.api_key,
        )
        if hasattr(DEFAULT_STORE, "log_observe_event"):
            await DEFAULT_STORE.log_observe_event(payload.workspace_id, result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
