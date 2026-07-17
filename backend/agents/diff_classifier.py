"""surgical re research classifier — identifies affected nodes on pivot"""
from __future__ import annotations

import json
import re
from typing import Any

from agents.store_protocol import GraphStore, ResearchTask, get_store, publish_workspace_update
from graph.schema import NodeStatus, NodeType
from llm.gemini import generate_pro
from sse.feed import feed

SYSTEM = """Classify a user's pivot against the startup graph.
Return ONLY JSON: nodes_affected, nodes_unchanged, requery_needed, spawn_researcher.
Use node type strings from the schema.
"""

ALL_NODES = [n.value for n in NodeType]


async def classify_pivot(workspace_id: str, message: str, store: GraphStore | None = None, enqueue: bool = True) -> dict[str, Any]:
    store = store or get_store()
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    prompt = json.dumps({"message": message, "workspace": workspace.model_dump(mode="json")}, indent=2)[:16000]
    try:
        data = _parse_json(await generate_pro(prompt, system=SYSTEM))
    except Exception:
        data = _heuristic(message)
    affected = [n for n in data.get("nodes_affected", []) if n in ALL_NODES]
    unchanged = [n for n in data.get("nodes_unchanged", []) if n in ALL_NODES and n not in affected]
    if not affected:
        affected = _heuristic(message)["nodes_affected"]
    if not unchanged:
        unchanged = [n for n in ALL_NODES if n not in affected]
    result = {
        "nodes_affected": affected,
        "nodes_unchanged": unchanged,
        "requery_needed": _as_bool(data.get("requery_needed"), bool(affected)),
        "spawn_researcher": _as_bool(data.get("spawn_researcher"), bool(affected)),
    }
    await feed.publish(
        workspace_id,
        {
            "text": f"[Diff Classifier] Pivot detected. Affected nodes: {', '.join(affected)}. Preserved: {', '.join(unchanged[:4])}.",
            "type": "info",
        },
    )
    for node in workspace.nodes:
        if node.type.value in affected and node.type != NodeType.CORE_IDEA:
            updated = node.model_copy(deep=True)
            updated.confidence = 0
            updated.status = NodeStatus.BLOCKING
            updated.active_agents = []
            updated.agent_notes = f"Awaiting user approval for targeted re-research after pivot: {message}"
            await store.update_node(workspace_id, updated)
    refreshed = await store.get_workspace(workspace_id)
    if refreshed is not None:
        await publish_workspace_update(workspace_id, refreshed)
    if enqueue and result["spawn_researcher"]:
        for i, node_type in enumerate(affected, start=1):
            tools = ["reddit", "firecrawl"] if node_type in {"audience", "revenue", "market_intelligence"} else ["firecrawl"]
            if node_type == "tech_stack":
                tools = ["github", "firecrawl"]
            await store.enqueue_task(
                ResearchTask(
                    workspace_id=workspace_id,
                    task=f"Re-research {node_type.replace('_', ' ')} after pivot: {message}",
                    type=node_type,
                    tools=tools,
                    priority=i,
                )
            )
    return result


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _heuristic(message: str) -> dict[str, Any]:
    msg = message.lower()
    affected: set[str] = set()
    if any(w in msg for w in ["audience", "customer", "segment", "persona", "restaurant", "kitchen"]):
        affected.update(["audience", "competitors", "revenue"])
    if any(w in msg for w in ["price", "monet", "business model", "subscription"]):
        affected.add("revenue")
    if any(w in msg for w in ["feature", "product", "mvp", "workflow"]):
        affected.add("product_vision")
    if any(w in msg for w in ["stack", "tech", "integration", "api"]):
        affected.add("tech_stack")
    if not affected:
        affected.update(["audience", "market_intelligence", "competitors"])
    return {"nodes_affected": sorted(affected), "nodes_unchanged": [n for n in ALL_NODES if n not in affected], "requery_needed": True, "spawn_researcher": True}


def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
        if match:
            return json.loads(match.group(1))
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise
