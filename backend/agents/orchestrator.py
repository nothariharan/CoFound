"""master orchestrator — reads graph state, spawns specialist agents"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from uuid import uuid4

from agents.dialogue import synthesize_dialogue
from agents.planner import plan
from agents.researcher import run_researchers
from agents.store_protocol import GraphStore, ResearchTask, publish_workspace_update
from mdb_mcp.agent_store import get_agent_store
from graph.schema import CoreIdeaData, CoreIdeaNode, NodeStatus, NodeType, status_from_confidence
from llm.gemini import generate_pro
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
    store: GraphStore | None = None,
    agents_active: int = 2,
    run_inline: bool = False,
) -> OrchestratorResult:
    """read graph → planner tasks → kick researchers → sse the whole way"""

    store = store or get_agent_store()
    session_id = str(uuid4())
    # every step publishes to sse so the canvas feels alive
    await feed.publish(workspace_id, {"text": "[Orchestrator] Session started. Reading graph state...", "type": "info"})
    await feed.publish(workspace_id, {"text": "[MongoDB MCP] Reading workspace via find", "type": "info"})
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        await feed.publish(workspace_id, {"text": "[Orchestrator] Workspace not found.", "type": "error"})
        raise ValueError(f"Workspace not found: {workspace_id}")

    tasks = await plan(workspace, store) if _needs_research(workspace, trigger) else []
    await feed.publish(
        workspace_id,
        {"text": f"[Planner/ADK] Queued {len(tasks)} research tasks for trigger={trigger}.", "type": "info"},
    )

    worker_count = min(max(1, agents_active), max(1, len(tasks))) if tasks else 0
    if worker_count:
        coro = _run_and_finalize(workspace_id, store, worker_count, session_id)
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


async def _run_and_finalize(workspace_id: str, store: GraphStore, worker_count: int, session_id: str) -> None:
    await run_researchers(workspace_id, store=store, worker_count=worker_count, session_id=session_id)
    await _clarify_core_idea(workspace_id, store)
    workspace = await store.get_workspace(workspace_id)
    if workspace is not None:
        await publish_workspace_update(workspace_id, workspace)
    try:
        dialogue = await synthesize_dialogue(workspace_id, store=store)
        await feed.publish(
            workspace_id,
            {
                "text": f"[Dialogue Agent] {dialogue['question']}",
                "type": "info",
                "dialogue": dialogue,
            },
        )
    except Exception as exc:
        await feed.publish(workspace_id, {"text": f"[Dialogue Agent] Could not synthesize question: {exc}", "type": "error"})


async def _clarify_core_idea(workspace_id: str, store: GraphStore) -> None:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        return
    core = next((node for node in workspace.nodes if node.type == NodeType.CORE_IDEA), None)
    if core is None:
        return
    prompt = json.dumps(workspace.model_dump(mode="json"), indent=2)[:16000]
    try:
        raw = await generate_pro(
            prompt,
            system=(
                "Sharpen the core startup idea from the graph. Return ONLY JSON with "
                "problem, solution, one_liner, confidence."
            ),
        )
        data = json.loads(raw)
    except Exception:
        return
    existing_data = getattr(core, "data", CoreIdeaData())
    updated = CoreIdeaNode(
        **core.model_dump(mode="python", exclude={"data"}),
        data=CoreIdeaData(
            problem=str(data.get("problem") or existing_data.problem or core.summary),
            solution=str(data.get("solution") or existing_data.solution or ""),
            one_liner=str(data.get("one_liner") or core.summary)[:240],
        ),
    )
    updated.summary = updated.data.one_liner
    updated.agent_notes = f"Problem: {updated.data.problem}\nSolution: {updated.data.solution}".strip()
    try:
        updated.confidence = max(core.confidence, min(100, int(data.get("confidence", core.confidence))))
    except (TypeError, ValueError):
        updated.confidence = core.confidence
    updated.status = status_from_confidence(updated.confidence)
    await store.update_node(workspace_id, updated)


def _needs_research(workspace, trigger: str) -> bool:
    if trigger in {"session_start", "pivot", "manual"}:
        return True
    return any(
        getattr(n, "confidence", 0) < 80 and getattr(n, "status", None) != NodeStatus.LOCKED
        for n in workspace.nodes
    )
