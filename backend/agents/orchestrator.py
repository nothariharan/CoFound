"""Master orchestrator — reads graph state, spawns specialist agents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import uuid4

from agents.planner import plan
from agents.researcher import run_researchers
from agents.store_protocol import DEFAULT_STORE, GraphStore, ResearchTask
from sse.feed import feed


@dataclass
class OrchestratorResult:
    session_id: str
    tasks_queued: int
    agents_active: int
    tasks: list[ResearchTask]


async def spawn_research_session(
    workspace_id: str,
    trigger: str = "manual",
    store: GraphStore = DEFAULT_STORE,
    agents_active: int = 2,
    run_inline: bool = False,
) -> OrchestratorResult:
    """Read workspace, create tasks if needed, and start researcher workers."""

    session_id = str(uuid4())
    await feed.publish(workspace_id, {"text": "[Orchestrator] Session started. Reading graph state...", "type": "info"})
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        await feed.publish(workspace_id, {"text": "[Orchestrator] Workspace not found.", "type": "error"})
        raise ValueError(f"Workspace not found: {workspace_id}")

    tasks = await plan(workspace, store) if _needs_research(workspace, trigger) else []
    await feed.publish(
        workspace_id,
        {"text": f"[Planner] Queued {len(tasks)} research tasks for trigger={trigger}.", "type": "info"},
    )

    worker_count = min(max(1, agents_active), max(1, len(tasks))) if tasks else 0
    if worker_count:
        coro = run_researchers(workspace_id, store=store, worker_count=worker_count, session_id=session_id)
        if run_inline:
            await coro
        else:
            asyncio.create_task(coro)
        await feed.publish(
            workspace_id,
            {"text": f"[Orchestrator] {worker_count} researchers active. Streaming updates.", "type": "info"},
        )
    else:
        await feed.publish(workspace_id, {"text": "[Orchestrator] No research needed.", "type": "done"})

    return OrchestratorResult(session_id=session_id, tasks_queued=len(tasks), agents_active=worker_count, tasks=tasks)


def _needs_research(workspace, trigger: str) -> bool:
    if trigger in {"session_start", "pivot", "manual"}:
        return True
    return any(getattr(n, "confidence", 0) < 80 and getattr(n, "status", "") != "locked" for n in workspace.nodes)
