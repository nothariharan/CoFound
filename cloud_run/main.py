"""Standalone ADK Planner service for Cloud Run / Render deployment."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

APP_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = APP_ROOT.parent / "backend"
if BACKEND_ROOT.exists():
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
elif str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from agents.adk.runner import run_planner_agent  # noqa: E402

app = FastAPI(title="CoFounder ADK Planner Service", version="0.1.0")


class PlanRequest(BaseModel):
    workspace: dict
    knowledge_base_hints: list[dict] | None = None


class PlanResponse(BaseModel):
    raw: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "agent": "cofounder_planner", "framework": "google-adk"}


@app.post("/plan", response_model=PlanResponse)
async def plan_workspace(payload: PlanRequest) -> PlanResponse:
    prompt = json.dumps(
        {
            "workspace": payload.workspace,
            "knowledge_base_hints": payload.knowledge_base_hints or [],
            "instructions": "Produce 6-10 focused research tasks as JSON.",
        },
        indent=2,
    )
    try:
        raw = await run_planner_agent(prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ADK Planner failed: {exc}") from exc
    return PlanResponse(raw=raw)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(__import__("os").getenv("PORT", "8080")))
