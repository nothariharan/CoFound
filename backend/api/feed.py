import asyncio
import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(tags=["feed"])

DEMO_LINES = [
    "[Orchestrator] Session started. Reading graph state...",
    "[Planner] Decomposing idea into research tasks...",
    "[Researcher R1] Queued: market intelligence scan",
    "[Researcher R2] Queued: competitor discovery",
    "[Orchestrator] 2 agents active. Streaming updates.",
]


@router.get("/feed")
async def agent_feed(request: Request, workspace_id: str | None = None):
    async def event_generator():
        for line in DEMO_LINES:
            if await request.is_disconnected():
                break
            yield {"event": "message", "data": json.dumps({"text": line, "type": "info"})}
            await asyncio.sleep(0.8)
        while not await request.is_disconnected():
            yield {"event": "ping", "data": json.dumps({"text": "", "type": "ping"})}
            await asyncio.sleep(15)

    return EventSourceResponse(event_generator())
