"""Agent spawn/status routes — Day 3-4."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.agents.diff_classifier import classify_pivot # Corrected import
from backend.agents.growth_agent import recommend_priority # Corrected import
from backend.agents.orchestrator import spawn_research_session # Corrected import
from backend.agents.store_protocol import DEFAULT_STORE # Corrected import

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
        return await classify_pivot(payload.workspace_id, payload.message, store=DEFAULT_STORE, enqueue=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/priority")
async def priority(workspace_id: str = Query(...)):
    try:
        return await recommend_priority(workspace_id, store=DEFAULT_STORE)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
