from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from sse.feed import feed

router = APIRouter(tags=["feed"])


@router.get("/feed")
async def agent_feed(request: Request, workspace_id: str | None = None):
    stream_id = workspace_id or "global"

    async def event_generator():
        async for event in feed.stream(stream_id, heartbeat_seconds=15):
            if await request.is_disconnected():
                break
            yield feed.encode(event)

    return EventSourceResponse(event_generator())
