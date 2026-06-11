"""Task manifest generator — decomposes idea into research tasks."""

from __future__ import annotations

import json
import re
from typing import Any

from agents.adk.runner import run_planner_agent
from agents.store_protocol import GraphStore, ResearchTask
from graph.schema import WorkspaceDocument
from sse.feed import feed

PLANNER_SYSTEM = """You are CoFound's Planner agent.
Return ONLY JSON: {"tasks":[{"task":str,"type":node_type,"tools":[str],"priority":int}]}.
Create 6-10 focused research tasks. Use only these tools: reddit, scrapling, firecrawl, github.
Node types: audience, market_intelligence, competitors, revenue, product_vision, tech_stack.
"""


async def plan(workspace: WorkspaceDocument, store: GraphStore) -> list[ResearchTask]:
    """Create and enqueue a task manifest for a workspace."""

    await feed.publish(
        workspace.idea_id,
        {"text": "[MongoDB MCP] Knowledge base search via aggregate", "type": "info"},
    )
    kb = await store.search_knowledge_base(_workspace_brief(workspace), limit=5)
    prompt = json.dumps(
        {
            "workspace": workspace.model_dump(mode="json"),
            "knowledge_base_hints": kb,
            "instructions": "Produce 6-10 focused research tasks as JSON.",
        },
        indent=2,
    )
    try:
        raw = await run_planner_agent(prompt)
        manifest = _parse_json(raw)
        items = manifest.get("tasks") if isinstance(manifest, dict) else manifest
    except Exception:
        items = _fallback_tasks(workspace)
    if not isinstance(items, list):
        items = _fallback_tasks(workspace)

    tasks: list[ResearchTask] = []
    for i, item in enumerate(items[:10], start=1):
        if not isinstance(item, dict):
            continue
        task = ResearchTask(
            workspace_id=workspace.idea_id,
            task=str(item.get("task") or item.get("query") or f"Research task {i}"),
            type=_node_type(item.get("type")),
            tools=_tool_list(item.get("tools")),
            priority=_priority(item.get("priority"), i),
            query=str(item["query"]) if item.get("query") else None,
        )
        await store.enqueue_task(task)
        tasks.append(task)

    if not tasks:
        for item in _fallback_tasks(workspace):
            task = ResearchTask(workspace_id=workspace.idea_id, **item)
            await store.enqueue_task(task)
            tasks.append(task)
    return tasks


def _node_type(value: Any) -> str:
    allowed = {"audience", "market_intelligence", "competitors", "revenue", "product_vision", "tech_stack"}
    aliases = {"market": "market_intelligence", "persona": "audience", "customers": "audience"}
    cleaned = aliases.get(str(value or "").lower().strip(), str(value or "").lower().strip())
    return cleaned if cleaned in allowed else "market_intelligence"


def _tool_list(value: Any) -> list[str]:
    if isinstance(value, str):
        raw = re.split(r"[,\s]+", value)
    elif isinstance(value, list):
        raw = value
    else:
        raw = ["firecrawl", "reddit"]
    allowed = {"reddit", "scrapling", "firecrawl", "github"}
    aliases = {"exa": "scrapling", "gummysearch": "scrapling", "web": "scrapling", "producthunt": "firecrawl", "product_hunt": "firecrawl"}
    tools = [aliases.get(str(t).lower().strip(), str(t).lower().strip()) for t in raw if str(t).strip()]
    tools = [tool for tool in tools if tool in allowed]
    return tools or ["firecrawl", "reddit"]


def _priority(value: Any, fallback: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return fallback


def _workspace_brief(workspace: WorkspaceDocument) -> str:
    core = next((n for n in workspace.nodes if n.type.value == "core_idea"), None)
    if core and hasattr(core, "data") and core.data.problem:
        return core.data.problem[:400]
    return (core.summary if core else workspace.workspace_name) or workspace.workspace_name


def _parse_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
        if match:
            return json.loads(match.group(1))
        start = min([i for i in [text.find("{"), text.find("[")] if i >= 0], default=-1)
        end = max(text.rfind("}"), text.rfind("]"))
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _fallback_tasks(workspace: WorkspaceDocument) -> list[dict[str, Any]]:
    idea = _workspace_brief(workspace)
    return [
        {"task": f"Mine Reddit for urgent pain points around: {idea}", "type": "audience", "tools": ["reddit"], "priority": 1},
        {"task": f"Estimate market demand and timing for: {idea}", "type": "market_intelligence", "tools": ["firecrawl", "reddit"], "priority": 2},
        {"task": f"Find direct and indirect competitors for: {idea}", "type": "competitors", "tools": ["firecrawl"], "priority": 3},
        {"task": f"Validate willingness to pay and pricing anchors for: {idea}", "type": "revenue", "tools": ["reddit", "firecrawl"], "priority": 4},
        {"task": f"Identify an MVP wedge and product promise for: {idea}", "type": "product_vision", "tools": ["firecrawl"], "priority": 5},
        {"task": f"Assess technical feasibility, integrations, and build risks for: {idea}", "type": "tech_stack", "tools": ["github", "firecrawl"], "priority": 6},
    ]
