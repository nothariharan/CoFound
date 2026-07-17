"""tool schemas and executors for the conversational orchestrator"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

from agents.diff_classifier import classify_pivot
from agents.export_agent import generate_export
from agents.growth_agent import handoff_target_node, recommend_priority
from agents.orchestrator import spawn_research_session
from agents.researcher import run_researchers
from agents.store_protocol import GraphStore, ResearchTask, get_store, publish_workspace_update
from graph.schema import BaseNode, NodeStatus, NodeType, node_agent_id
from sse.feed import feed

TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "get_workspace_summary",
        "description": "Get a structured summary of the startup workspace: nodes, confidence, active agents, and gaps.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_today_priority",
        "description": "Get today's highest-ROI priority action from the growth agent without starting research.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "start_node_research",
        "description": "Start research on a specific knowledge-graph node. Use when the user asks to research, investigate, or approve a node.",
        "parameters": {
            "type": "object",
            "properties": {
                "node_type": {
                    "type": "string",
                    "description": "One of: audience, market_intelligence, competitors, revenue, product_vision, tech_stack, build, launch, observe, growth",
                },
                "user_context": {
                    "type": "string",
                    "description": "Optional extra context from the user's request.",
                },
            },
            "required": ["node_type"],
        },
    },
    {
        "name": "spawn_research_agents",
        "description": "Create new research nodes on the graph and spawn parallel research agents for custom topics. Use when the user asks to research, investigate, or spawn agents on one or more topics — especially current solutions, competitors, or user pain related to their problem.",
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "description": "1-3 research topics. Each creates a new node connected to the graph.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Short node title shown on the graph."},
                            "description": {"type": "string", "description": "What the research agent should investigate."},
                            "parent_node_type": {
                                "type": "string",
                                "description": "Canonical node to connect to: core_idea, audience, competitors, market_intelligence, etc.",
                            },
                        },
                        "required": ["title", "description"],
                    },
                },
                "user_message": {
                    "type": "string",
                    "description": "Optional original user message for topic inference when topics array is empty.",
                },
            },
        },
    },
    {
        "name": "spawn_research_session",
        "description": "Bulk-spawn the planner and multiple researcher agents across the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "trigger": {
                    "type": "string",
                    "description": "Trigger reason, e.g. manual or session_start.",
                },
            },
        },
    },
    {
        "name": "handoff_priority",
        "description": "Hand off today's priority to the orchestrator and start research on the recommended node.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "spawn_custom_task",
        "description": "Spawn a custom research task on the graph.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "node_type": {
                    "type": "string",
                    "description": "Optional node type to attach the task to.",
                },
            },
            "required": ["title", "description"],
        },
    },
    {
        "name": "pivot_idea",
        "description": "Classify a pivot message and surgically reset affected nodes.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The user's pivot description."},
            },
            "required": ["message"],
        },
    },
    {
        "name": "trigger_export",
        "description": "Generate the export zip for the workspace.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "request_ui_action",
        "description": "Request a frontend UI action such as selecting a node or opening a dialog.",
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "description": "One of: select_node, open_settings, open_export, open_journal, open_integrations",
                },
                "node_type": {
                    "type": "string",
                    "description": "Required when action_type is select_node.",
                },
                "integration_id": {
                    "type": "string",
                    "description": "Required when action_type is open_integrations (github or posthog).",
                },
            },
            "required": ["action_type"],
        },
    },
]


async def execute_tool(
    name: str,
    args: dict[str, Any],
    workspace_id: str,
    store: GraphStore | None = None,
) -> dict[str, Any]:
    """run a tool and return a json serializable result"""
    store = store or get_store()

    if name == "get_workspace_summary":
        return await _get_workspace_summary(workspace_id, store)
    if name == "get_today_priority":
        return await recommend_priority(workspace_id, store=store)
    if name == "start_node_research":
        return await _start_node_research(
            workspace_id,
            args.get("node_type", ""),
            args.get("user_context"),
            store=store,
        )
    if name == "spawn_research_agents":
        return await _spawn_research_agents(
            workspace_id,
            args.get("topics") or [],
            str(args.get("user_message") or ""),
            store=store,
        )
    if name == "spawn_research_session":
        result = await spawn_research_session(
            workspace_id,
            trigger=str(args.get("trigger") or "manual"),
            store=store,
        )
        return {
            "session_id": result.session_id,
            "tasks_queued": result.tasks_queued,
            "agents_active": result.agents_active,
        }
    if name == "handoff_priority":
        return await _handoff_priority(workspace_id, store)
    if name == "spawn_custom_task":
        return await _spawn_custom_task(
            workspace_id,
            str(args.get("title") or ""),
            str(args.get("description") or ""),
            args.get("node_type"),
            store=store,
        )
    if name == "pivot_idea":
        return await classify_pivot(
            workspace_id,
            str(args.get("message") or ""),
            store=store,
            enqueue=False,
        )
    if name == "trigger_export":
        return await generate_export(workspace_id, store=store)
    if name == "request_ui_action":
        return {
            "ok": True,
            "ui_action": {
                "type": args.get("action_type"),
                "payload": {
                    k: v
                    for k, v in {
                        "node_type": args.get("node_type"),
                        "integration_id": args.get("integration_id"),
                    }.items()
                    if v
                },
            },
        }
    return {"error": f"Unknown tool: {name}"}


async def _get_workspace_summary(workspace_id: str, store: GraphStore) -> dict[str, Any]:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    nodes = []
    active_count = 0
    for node in workspace.nodes:
        if node.active_agents:
            active_count += 1
        nodes.append(
            {
                "type": node.type.value,
                "title": node.title,
                "confidence": node.confidence,
                "status": node.status.value,
                "active_agents": node.active_agents,
                "summary": (node.summary or node.agent_notes or "")[:200],
            }
        )

    return {
        "workspace_name": workspace.workspace_name,
        "idea_id": workspace.idea_id,
        "nodes": nodes,
        "active_research_count": active_count,
        "export_ready": getattr(workspace, "export_ready", False),
    }


async def _start_node_research(
    workspace_id: str,
    node_type_raw: str,
    user_context: str | None,
    *,
    store: GraphStore,
) -> dict[str, Any]:
    try:
        node_type = NodeType(str(node_type_raw).strip().lower())
    except ValueError as exc:
        return {"error": f"Invalid node_type: {node_type_raw}"}

    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    node = next((item for item in workspace.nodes if item.type == node_type), None)
    if node is None:
        return {"error": f"Node not found: {node_type.value}"}
    if node.type == NodeType.CORE_IDEA:
        return {"error": "Core Idea is framed automatically and does not need research approval"}
    if node.status == NodeStatus.LOCKED:
        return {"error": f"{node.title or node.type.value} is locked until prerequisites are met"}
    node = await _clear_stale_active_agent(workspace_id, node, store)
    if node.active_agents:
        return {
            "error": f"{node.title or node.type.value} research is already running",
            "already_running": True,
            "node_type": node_type.value,
            "node_title": node.title or node.type.value,
        }

    agent_label = node_agent_id(node_type)
    approved = node.model_copy(deep=True)
    approved.active_agents = [agent_label]
    await store.update_node(workspace_id, approved)

    core_node = next((item for item in workspace.nodes if item.type == NodeType.CORE_IDEA), None)
    idea_description = ""
    if core_node and hasattr(core_node, "data"):
        idea_description = core_node.data.problem or core_node.summary or ""

    task_text = _node_task(node_type, workspace.workspace_name, user_context, idea_description)
    task = ResearchTask(
        workspace_id=workspace_id,
        task=task_text,
        type=node_type.value,
        tools=_node_tools(node_type),
        priority=1,
        node_id=node.node_id,
    )
    await store.enqueue_task(task)
    asyncio.create_task(run_researchers(workspace_id, store=store, worker_count=1))
    await feed.publish(
        workspace_id,
        {
            "text": f"[Orchestrator] Research started for {node.title or node.type.value}.",
            "type": "info",
            "node_id": node.node_id,
        },
    )
    workspace = await store.get_workspace(workspace_id)
    if workspace is not None:
        await publish_workspace_update(workspace_id, workspace)

    return {
        "session_id": task.task_id,
        "tasks_queued": 1,
        "agents_active": 1,
        "node_type": node_type.value,
        "node_title": node.title or node.type.value,
    }


async def _handoff_priority(workspace_id: str, store: GraphStore) -> dict[str, Any]:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    priority = await recommend_priority(workspace_id, store=store)
    node_type_value = priority.get("node_type") or ""
    try:
        node_type = NodeType(node_type_value)
    except ValueError:
        return {"error": "No handoff target available for this workspace"}

    node = next((item for item in workspace.nodes if item.type == node_type), None)
    if node is None:
        return {"error": f"Node not found: {node_type.value}"}
    if node.status == NodeStatus.LOCKED:
        target = handoff_target_node(workspace)
        if target is None:
            return {"error": "No unlocked research nodes are available for handoff"}
        node = target
        node_type = target.type

    user_context = f"Today's priority: {priority.get('action', '').strip()}. Why: {priority.get('reason', '').strip()}".strip()
    result = await _start_node_research(workspace_id, node_type.value, user_context, store=store)
    if "error" not in result:
        await feed.publish(
            workspace_id,
            {
                "text": f"[Orchestrator] Handed off today's priority to {node.title or node.type.value}.",
                "type": "info",
                "node_id": node.node_id,
            },
        )
        result["priority"] = priority
    return result


async def _spawn_custom_task(
    workspace_id: str,
    title: str,
    description: str,
    node_type_raw: str | None,
    *,
    store: GraphStore,
) -> dict[str, Any]:
    title = title.strip()
    description = description.strip()
    if not title or not description:
        return {"error": "Title and description are required"}

    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    node_type = _infer_node_type(f"{title} {description}")
    if node_type_raw:
        try:
            node_type = NodeType(str(node_type_raw).strip().lower())
        except ValueError:
            pass

    node = next((item for item in workspace.nodes if item.type == node_type), None)
    if node is None:
        return {"error": f"Node not found: {node_type.value}"}
    if node.status == NodeStatus.LOCKED:
        return {"error": f"{node.title or node.type.value} is locked until prerequisites are met"}
    if node.active_agents:
        return {"error": f"{node.title or node.type.value} already has an active agent"}

    agent_id = node_agent_id(node_type)
    approved = node.model_copy(deep=True)
    approved.active_agents = [agent_id]
    await store.update_node(workspace_id, approved)

    core_node = next((item for item in workspace.nodes if item.type == NodeType.CORE_IDEA), None)
    idea_description = ""
    if core_node and hasattr(core_node, "data"):
        idea_description = core_node.data.problem or core_node.summary or ""

    query = f"{title}: {description}"
    if idea_description:
        query = f"{query}. Startup context: {idea_description[:400]}"

    task = ResearchTask(
        workspace_id=workspace_id,
        task=query,
        type=node_type.value,
        tools=["firecrawl", "reddit"],
        priority=1,
        node_id=node.node_id,
        query=query,
    )
    await store.enqueue_task(task)
    asyncio.create_task(run_researchers(workspace_id, store=store, worker_count=1))
    await feed.publish(
        workspace_id,
        {
            "text": f"[Orchestrator] Spawned custom agent for: {title}",
            "type": "info",
            "node_id": node.node_id,
        },
    )
    workspace = await store.get_workspace(workspace_id)
    if workspace is not None:
        await publish_workspace_update(workspace_id, workspace)

    return {
        "session_id": task.task_id,
        "tasks_queued": 1,
        "agents_active": 1,
        "title": title,
        "node_type": node_type.value,
    }


async def _spawn_research_agents(
    workspace_id: str,
    topics_raw: list[dict[str, Any]] | None,
    user_message: str,
    *,
    store: GraphStore,
) -> dict[str, Any]:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    topics = _normalize_topics(topics_raw)
    inferred = _infer_research_topics(user_message, workspace)
    if not topics:
        topics = inferred
    elif len(topics) < len(inferred) and (_wants_multi_research(user_message) or len(topics) == 1):
        topics = inferred
    if not topics:
        return {"error": "No research topics provided"}

    topics = topics[:3]
    core_node = next((item for item in workspace.nodes if item.type == NodeType.CORE_IDEA), None)
    idea_description = ""
    if core_node and hasattr(core_node, "data"):
        idea_description = core_node.data.problem or core_node.summary or ""

    created: list[dict[str, str]] = []
    for topic in topics:
        title = str(topic.get("title") or "Research topic").strip()
        description = str(topic.get("description") or title).strip()
        parent_node = _resolve_parent_node(workspace, topic.get("parent_node_type"), title, description)
        node_id = str(uuid4())
        short_id = node_id[:8]
        node = BaseNode(
            node_id=node_id,
            type=NodeType.CUSTOM_RESEARCH,
            title=title,
            summary=description[:240],
            parent_node_id=parent_node.node_id,
            active_agents=[f"agent_research_{short_id}"],
            status=NodeStatus.BLOCKING,
        )
        await store.update_node(workspace_id, node)

        query = f"{title}: {description}"
        if idea_description:
            query = f"{query}. Startup context: {idea_description[:400]}"

        task = ResearchTask(
            workspace_id=workspace_id,
            task=query,
            type=NodeType.CUSTOM_RESEARCH.value,
            tools=["firecrawl", "reddit"],
            priority=1,
            node_id=node_id,
            query=query,
        )
        await store.enqueue_task(task)
        created.append(
            {
                "node_id": node_id,
                "title": title,
                "parent_node_id": parent_node.node_id,
                "parent_title": parent_node.title or parent_node.type.value,
            }
        )
        await feed.publish(
            workspace_id,
            {
                "text": f"[Orchestrator] Spawned research agent: {title}",
                "type": "info",
                "node_id": node_id,
            },
        )

    worker_count = 1
    asyncio.create_task(run_researchers(workspace_id, store=store, worker_count=worker_count))
    workspace = await store.get_workspace(workspace_id)
    if workspace is not None:
        await publish_workspace_update(workspace_id, workspace)

    return {
        "nodes_created": created,
        "tasks_queued": len(created),
        "agents_active": worker_count,
    }


def _normalize_topics(topics_raw: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    topics: list[dict[str, str]] = []
    for item in topics_raw or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        description = str(item.get("description") or title).strip()
        if not title:
            continue
        topic: dict[str, str] = {"title": title, "description": description}
        parent = item.get("parent_node_type")
        if parent:
            topic["parent_node_type"] = str(parent).strip().lower()
        topics.append(topic)
    return topics


def _wants_multi_research(message: str) -> bool:
    lowered = (message or "").lower()
    return any(
        k in lowered
        for k in (
            "3 agent",
            "3 research",
            "three agent",
            "three research",
            "parallel",
            "multiple topic",
            "separate topic",
            "sub-agent",
            "sub agent",
        )
    )


def _infer_research_topics(message: str, workspace) -> list[dict[str, str]]:
    core = next((n for n in workspace.nodes if n.type == NodeType.CORE_IDEA), None)
    problem = ""
    if core and hasattr(core, "data"):
        problem = core.data.problem or core.summary or ""
    problem = (problem or workspace.workspace_name).strip()[:220]
    lowered = (message or "").lower()

    if any(k in lowered for k in ("research", "investigate", "spawn", "agent", "solution", "current", "topic")):
        return [
            {
                "title": "Existing solutions landscape",
                "description": f"Map current products and services already addressing: {problem}",
                "parent_node_type": "core_idea",
            },
            {
                "title": "Competitor gap analysis",
                "description": f"Identify gaps and weaknesses in existing solutions for: {problem}",
                "parent_node_type": "competitors",
            },
            {
                "title": "User pain with current tools",
                "description": f"Find user complaints and pain points with current solutions for: {problem}",
                "parent_node_type": "audience",
            },
        ]
    if message.strip():
        return [{"title": "Custom research", "description": message.strip(), "parent_node_type": "core_idea"}]
    return []


def _resolve_parent_node(workspace, parent_node_type_raw: str | None, title: str, description: str):
    core = next((n for n in workspace.nodes if n.type == NodeType.CORE_IDEA), None)
    fallback = core or workspace.nodes[0]

    if parent_node_type_raw:
        try:
            node_type = NodeType(str(parent_node_type_raw).strip().lower())
            match = next((n for n in workspace.nodes if n.type == node_type), None)
            if match is not None and match.status != NodeStatus.LOCKED:
                return match
        except ValueError:
            pass

    inferred = _infer_node_type(f"{title} {description}")
    match = next((n for n in workspace.nodes if n.type == inferred), None)
    if match is not None and match.status != NodeStatus.LOCKED:
        return match
    return fallback


async def _clear_stale_active_agent(workspace_id: str, node: BaseNode, store: GraphStore) -> BaseNode:
    if not node.active_agents:
        return node
    task_queue = getattr(store, "task_queue", None)
    if isinstance(task_queue, list):
        busy = any(
            t.node_id == node.node_id and t.status in {"pending", "running"}
            for t in task_queue
            if getattr(t, "workspace_id", workspace_id) == workspace_id
        )
        if not busy:
            cleared = node.model_copy(deep=True)
            cleared.active_agents = []
            await store.update_node(workspace_id, cleared)
            return cleared
    return node


def _node_task(node_type: NodeType, workspace_name: str, user_context: str | None, idea_description: str = "") -> str:
    label = node_type.value.replace("_", " ")
    context = idea_description.strip() or workspace_name
    suffix = f" User context: {user_context.strip()}" if user_context and user_context.strip() else ""
    return f"Research {label} for: {context}.{suffix}"


def _node_tools(node_type: NodeType) -> list[str]:
    if node_type in {NodeType.AUDIENCE, NodeType.REVENUE, NodeType.MARKET_INTELLIGENCE}:
        return ["reddit", "firecrawl"]
    if node_type == NodeType.TECH_STACK:
        return ["github", "firecrawl"]
    if node_type in {NodeType.BUILD, NodeType.LAUNCH}:
        return ["github", "firecrawl"]
    return ["firecrawl"]


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


def infer_tool_calls_from_message(message: str) -> list:
    from llm.types import ToolCall

    lowered = message.lower()
    if any(
        k in lowered
        for k in ("research", "investigate", "spawn", "agent", "solution", "current", "topic", "sub-agent", "sub agent")
    ):
        return [
            ToolCall(
                name="spawn_research_agents",
                args={"topics": [], "user_message": message},
                id="",
            )
        ]
    if "priority" in lowered and "hand" not in lowered:
        return [ToolCall(name="get_today_priority", args={}, id="")]
    if "hand" in lowered and "off" in lowered:
        return [ToolCall(name="handoff_priority", args={}, id="")]
    if "pivot" in lowered:
        return [ToolCall(name="pivot_idea", args={"message": message}, id="")]
    if "export" in lowered:
        return [ToolCall(name="trigger_export", args={}, id="")]
    if "settings" in lowered:
        return [ToolCall(name="request_ui_action", args={"action_type": "open_settings"}, id="")]
    if "journal" in lowered:
        return [ToolCall(name="request_ui_action", args={"action_type": "open_journal"}, id="")]
    if "show" in lowered and "audience" in lowered:
        return [ToolCall(name="request_ui_action", args={"action_type": "select_node", "node_type": "audience"}, id="")]
    if "show" in lowered and "competitor" in lowered:
        return [ToolCall(name="request_ui_action", args={"action_type": "select_node", "node_type": "competitors"}, id="")]
    if any(k in lowered for k in ("status", "update", "summary", "welcome")):
        return [ToolCall(name="get_workspace_summary", args={}, id="")]
    return [ToolCall(name="get_workspace_summary", args={}, id="")]


def tool_summary(name: str, result: dict[str, Any]) -> str:
    if result.get("already_running"):
        return f"{result.get('node_title', 'Node')} research is already running"
    if result.get("error"):
        return f"{name} failed: {result['error']}"
    if name == "get_workspace_summary":
        return f"Loaded workspace summary ({len(result.get('nodes', []))} nodes)"
    if name == "get_today_priority":
        return f"Priority: {result.get('action', 'unknown')}"
    if name == "start_node_research":
        return f"Started research on {result.get('node_title', result.get('node_type', 'node'))}"
    if name == "spawn_research_agents":
        nodes = result.get("nodes_created") or []
        titles = ", ".join(item.get("title", "topic") for item in nodes)
        return f"Spawned {len(nodes)} research agent(s): {titles}"
    if name == "spawn_research_session":
        return f"Spawned session with {result.get('tasks_queued', 0)} tasks"
    if name == "handoff_priority":
        return f"Handed off priority to {result.get('node_title', result.get('node_type', 'node'))}"
    if name == "spawn_custom_task":
        return f"Spawned custom task: {result.get('title', 'task')}"
    if name == "pivot_idea":
        affected = result.get("nodes_affected") or []
        return f"Pivot applied to {len(affected)} node(s)"
    if name == "trigger_export":
        return "Export generated"
    if name == "request_ui_action":
        action = (result.get("ui_action") or {}).get("type", "ui")
        return f"UI action: {action}"
    return f"Completed {name}"
