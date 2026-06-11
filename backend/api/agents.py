"""Agent spawn/status routes — Day 3-4."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agents.build_observer import observe_build
from agents.conversational_orchestrator import orchestrator_chat
from agents.dialogue import synthesize_dialogue
from agents.diff_classifier import classify_pivot
from agents.growth_agent import handoff_target_node, recommend_priority
from agents.observe_agent import observe_funnel
from agents.orchestrator import spawn_research_session
from agents.orchestrator_tools import _spawn_research_agents
from agents.researcher import run_researchers
from agents.store_protocol import ResearchTask, publish_workspace_update
from mdb_mcp.agent_store import get_agent_store
from graph.schema import NodeStatus, NodeType, node_agent_id
from sse.feed import feed

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


class ResearchNodeRequest(BaseModel):
    workspace_id: str
    node_type: NodeType
    user_context: str | None = None


class CustomTaskRequest(BaseModel):
    workspace_id: str
    title: str
    description: str
    node_type: NodeType | None = None


class ResearchTopic(BaseModel):
    title: str
    description: str
    parent_node_type: str | None = None


class SpawnResearchAgentsRequest(BaseModel):
    workspace_id: str
    topics: list[ResearchTopic] = []
    user_message: str | None = None


class SpawnResearchAgentsResponse(BaseModel):
    nodes_created: list[dict[str, str]]
    tasks_queued: int
    agents_active: int


class HandoffRequest(BaseModel):
    workspace_id: str


class OrchestratorChatRequest(BaseModel):
    workspace_id: str
    message: str
    history: list[dict[str, str]] | None = None


class OrchestratorChatResponse(BaseModel):
    reply: str
    speaking_text: str | None = None
    actions_taken: list[dict[str, str]] = []
    ui_actions: list[dict[str, object]] = []


@router.post("/orchestrator/chat", response_model=OrchestratorChatResponse)
async def orchestrator_chat_route(payload: OrchestratorChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    try:
        result = await orchestrator_chat(
            payload.workspace_id,
            payload.message,
            history=payload.history,
            store=get_agent_store(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OrchestratorChatResponse(
        reply=result["reply"],
        speaking_text=result.get("speaking_text"),
        actions_taken=result.get("actions_taken") or [],
        ui_actions=result.get("ui_actions") or [],
    )


@router.post("/agents/spawn", response_model=SpawnResponse)
async def spawn_agents(payload: SpawnRequest):
    try:
        result = await spawn_research_session(payload.workspace_id, trigger=payload.trigger, store=get_agent_store())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SpawnResponse(session_id=result.session_id, tasks_queued=result.tasks_queued, agents_active=result.agents_active)


@router.post("/agents/pivot")
async def pivot_agents(payload: PivotRequest):
    try:
        result = await classify_pivot(payload.workspace_id, payload.message, store=get_agent_store(), enqueue=False)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agents/research-node", response_model=SpawnResponse)
async def research_node(payload: ResearchNodeRequest):
    workspace = await get_agent_store().get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    node = next((item for item in workspace.nodes if item.type == payload.node_type), None)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {payload.node_type.value}")
    return await _start_node_research(
        payload.workspace_id,
        node,
        payload.node_type,
        payload.user_context,
        agent_label=node_agent_id(payload.node_type),
        feed_prefix="[User Approval]",
    )


@router.post("/agents/handoff-priority", response_model=SpawnResponse)
async def handoff_priority(payload: HandoffRequest):
    workspace = await get_agent_store().get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    priority = await recommend_priority(payload.workspace_id, store=get_agent_store())
    node_type_value = priority.get("node_type") or ""
    try:
        node_type = NodeType(node_type_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="No handoff target available for this workspace") from exc

    node = next((item for item in workspace.nodes if item.type == node_type), None)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_type.value}")
    if node.status == NodeStatus.LOCKED:
        target = handoff_target_node(workspace)
        if target is None:
            raise HTTPException(status_code=400, detail="No unlocked research nodes are available for handoff")
        node = target
        node_type = target.type

    user_context = f"Today's priority: {priority.get('action', '').strip()}. Why: {priority.get('reason', '').strip()}".strip()
    result = await _start_node_research(
        payload.workspace_id,
        node,
        node_type,
        user_context,
        agent_label=node_agent_id(node_type),
        feed_prefix="[Orchestrator Handoff]",
    )
    await feed.publish(
        payload.workspace_id,
        {
            "text": f"[Orchestrator] Handed off today's priority to {node.title or node.type.value}.",
            "type": "info",
            "node_id": node.node_id,
        },
    )
    return result


@router.post("/agents/custom-task", response_model=SpawnResponse)
async def custom_task(payload: CustomTaskRequest):
    workspace = await get_agent_store().get_workspace(payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    title = payload.title.strip()
    description = payload.description.strip()
    if not title or not description:
        raise HTTPException(status_code=400, detail="Title and description are required")

    node_type = payload.node_type or _infer_node_type(f"{title} {description}")
    node = next((item for item in workspace.nodes if item.type == node_type), None)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_type.value}")
    if node.status == NodeStatus.LOCKED:
        raise HTTPException(status_code=400, detail=f"{node.title or node.type.value} is locked until prerequisites are met")
    if node.active_agents:
        raise HTTPException(status_code=409, detail=f"{node.title or node.type.value} already has an active agent")

    agent_id = node_agent_id(node_type)
    approved = node.model_copy(deep=True)
    approved.active_agents = [agent_id]
    await get_agent_store().update_node(payload.workspace_id, approved)

    core_node = next((item for item in workspace.nodes if item.type == NodeType.CORE_IDEA), None)
    idea_description = ""
    if core_node and hasattr(core_node, "data"):
        idea_description = core_node.data.problem or core_node.summary or ""

    query = f"{title}: {description}"
    if idea_description:
        query = f"{query}. Startup context: {idea_description[:400]}"

    task = ResearchTask(
        workspace_id=payload.workspace_id,
        task=query,
        type=node_type.value,
        tools=["firecrawl", "reddit"],
        priority=1,
        node_id=node.node_id,
        query=query,
    )
    await get_agent_store().enqueue_task(task)
    asyncio.create_task(run_researchers(payload.workspace_id, store=get_agent_store(), worker_count=1))
    await feed.publish(
        payload.workspace_id,
        {
            "text": f"[Orchestrator] Spawned custom agent for: {title}",
            "type": "info",
            "node_id": node.node_id,
        },
    )
    workspace = await get_agent_store().get_workspace(payload.workspace_id)
    if workspace is not None:
        await publish_workspace_update(payload.workspace_id, workspace)
    return SpawnResponse(session_id=task.task_id, tasks_queued=1, agents_active=1)


@router.post("/agents/spawn-research-agents", response_model=SpawnResearchAgentsResponse)
async def spawn_research_agents(payload: SpawnResearchAgentsRequest):
    try:
        result = await _spawn_research_agents(
            payload.workspace_id,
            [topic.model_dump() for topic in payload.topics],
            str(payload.user_message or ""),
            store=get_agent_store(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result.get("error"):
        raise HTTPException(status_code=400, detail=str(result["error"]))
    return SpawnResearchAgentsResponse(
        nodes_created=result.get("nodes_created") or [],
        tasks_queued=int(result.get("tasks_queued") or 0),
        agents_active=int(result.get("agents_active") or 0),
    )


@router.get("/priority")
async def priority(workspace_id: str = Query(...)):
    try:
        return await recommend_priority(workspace_id, store=get_agent_store())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/agents/dialogue", response_model=DialogueResponse)
async def get_dialogue(workspace_id: str = Query(...)):
    try:
        result = await synthesize_dialogue(workspace_id, store=get_agent_store())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DialogueResponse(brief=result["brief"], question=result["question"])


@router.post("/agents/dialogue", response_model=DialogueResponse)
async def post_dialogue(payload: DialogueRequest):
    try:
        result = await synthesize_dialogue(payload.workspace_id, store=get_agent_store())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if payload.message:
        result["brief"] = f"{result['brief']} User context: {payload.message.strip()}"
    return DialogueResponse(brief=result["brief"], question=result["question"])


@router.post("/agents/observe")
async def observe_build_route(payload: ObserveBuildRequest):
    try:
        result = await observe_build(payload.workspace_id, payload.repo, store=get_agent_store(), token=payload.access_token)
        if hasattr(get_agent_store(), "log_build_event"):
            await get_agent_store().log_build_event(payload.workspace_id, result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _node_task(node_type: NodeType, workspace_name: str, user_context: str | None, idea_description: str = "") -> str:
    label = node_type.value.replace("_", " ")
    context = idea_description.strip() or workspace_name
    suffix = f" User context: {user_context.strip()}" if user_context and user_context.strip() else ""
    return f"Research {label} for: {context}.{suffix}"


async def _start_node_research(
    workspace_id: str,
    node,
    node_type: NodeType,
    user_context: str | None,
    *,
    agent_label: str,
    feed_prefix: str,
) -> SpawnResponse:
    if node.type == NodeType.CORE_IDEA:
        raise HTTPException(status_code=400, detail="Core Idea is framed automatically and does not need research approval")
    if node.status == NodeStatus.LOCKED:
        raise HTTPException(status_code=400, detail=f"{node.title or node.type.value} is locked until prerequisites are met")
    if node.active_agents:
        raise HTTPException(status_code=409, detail=f"{node.title or node.type.value} research is already running")

    workspace = await get_agent_store().get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    approved = node.model_copy(deep=True)
    approved.active_agents = [agent_label]
    await get_agent_store().update_node(workspace_id, approved)

    core_node = next((item for item in workspace.nodes if item.type == NodeType.CORE_IDEA), None)
    idea_description = ""
    if core_node and hasattr(core_node, "data"):
        idea_description = core_node.data.problem or core_node.summary or ""

    task = ResearchTask(
        workspace_id=workspace_id,
        task=_node_task(node_type, workspace.workspace_name, user_context, idea_description),
        type=node_type.value,
        tools=_node_tools(node_type),
        priority=1,
        node_id=node.node_id,
    )
    await get_agent_store().enqueue_task(task)
    asyncio.create_task(run_researchers(workspace_id, store=get_agent_store(), worker_count=1))
    await feed.publish(
        workspace_id,
        {"text": f"{feed_prefix} Research started for {node.title or node.type.value}.", "type": "info", "node_id": node.node_id},
    )
    workspace = await get_agent_store().get_workspace(workspace_id)
    if workspace is not None:
        await publish_workspace_update(workspace_id, workspace)
    return SpawnResponse(session_id=task.task_id, tasks_queued=1, agents_active=1)


def _infer_node_type(text: str) -> NodeType:
    lowered = text.lower()
    rules: list[tuple[tuple[str, ...], NodeType]] = [
        (("competitor", "alternative", "rival"), NodeType.COMPETITORS),
        (("audience", "customer", "persona", "user pain"), NodeType.AUDIENCE),
        (("pricing", "revenue", "monet", "willingness to pay"), NodeType.REVENUE),
        (("tech", "stack", "integration", "github", "build risk"), NodeType.TECH_STACK),
        (("product", "mvp", "feature", "vision", "wedge"), NodeType.PRODUCT_VISION),
        (("market", "demand", "timing", "tam"), NodeType.MARKET_INTELLIGENCE),
    ]
    for keywords, node_type in rules:
        if any(keyword in lowered for keyword in keywords):
            return node_type
    return NodeType.PRODUCT_VISION


def _node_tools(node_type: NodeType) -> list[str]:
    if node_type in {NodeType.AUDIENCE, NodeType.REVENUE, NodeType.MARKET_INTELLIGENCE}:
        return ["reddit", "firecrawl"]
    if node_type == NodeType.TECH_STACK:
        return ["github", "firecrawl"]
    if node_type in {NodeType.BUILD, NodeType.LAUNCH}:
        return ["github", "firecrawl"]
    return ["firecrawl"]


@router.post("/agents/observe-funnel")
async def observe_funnel_route(payload: ObserveFunnelRequest):
    try:
        result = await observe_funnel(
            payload.workspace_id,
            store=get_agent_store(),
            project_id=payload.project_id,
            api_key=payload.api_key,
        )
        if hasattr(get_agent_store(), "log_observe_event"):
            await get_agent_store().log_observe_event(payload.workspace_id, result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
