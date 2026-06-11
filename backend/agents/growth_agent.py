"""Growth recommendation generator — triggered on observe signals."""

from __future__ import annotations

import json
from typing import Any

from agents.store_protocol import GraphStore
from mdb_mcp.agent_store import get_agent_store
from graph.schema import NodeStatus, NodeType, WorkspaceDocument
from llm.gemini import generate_pro

HANDOFF_NODE_TYPES = {
    NodeType.AUDIENCE,
    NodeType.MARKET_INTELLIGENCE,
    NodeType.COMPETITORS,
    NodeType.REVENUE,
    NodeType.PRODUCT_VISION,
    NodeType.TECH_STACK,
}


async def recommend_priority(workspace_id: str, store: GraphStore | None = None, observe: dict[str, Any] | None = None) -> dict[str, str]:
    store = store or get_agent_store()
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    target = handoff_target_node(workspace)
    prompt = json.dumps({"workspace": workspace.model_dump(mode="json"), "observe": observe or {}}, indent=2)[:16000]
    try:
        raw = await generate_pro(
            prompt,
            system=(
                "Return JSON with action, reason, estimated_time, impact, node_type for today's highest-ROI startup task. "
                "node_type must be one of: audience, market_intelligence, competitors, revenue, product_vision, tech_stack."
            ),
        )
        data = json.loads(raw)
    except Exception:
        data = _fallback(workspace, target)

    fallback = _fallback(workspace, target)
    node_type = str(data.get("node_type") or fallback.get("node_type") or "")
    if node_type not in {item.value for item in HANDOFF_NODE_TYPES}:
        node_type = fallback["node_type"]

    result = {
        "action": str(data.get("action") or fallback["action"]),
        "reason": str(data.get("reason") or fallback["reason"]),
        "estimated_time": str(data.get("estimated_time") or fallback["estimated_time"]),
        "impact": str(data.get("impact") or fallback["impact"]),
        "node_type": node_type,
        "node_id": target.node_id if target else "",
    }
    return result


def handoff_target_node(workspace: WorkspaceDocument):
    candidates = [
        node
        for node in workspace.nodes
        if node.type in HANDOFF_NODE_TYPES and node.status != NodeStatus.LOCKED and not node.active_agents
    ]
    if not candidates:
        candidates = [
            node for node in workspace.nodes if node.type in HANDOFF_NODE_TYPES and node.status != NodeStatus.LOCKED
        ]
    if not candidates:
        return None
    return min(candidates, key=lambda node: node.confidence)


def _fallback(workspace: WorkspaceDocument, target=None) -> dict[str, str]:
    weak = target or handoff_target_node(workspace)
    label = weak.type.value.replace("_", " ") if weak else "audience"
    return {
        "action": f"Run 3 focused validation conversations about {label}",
        "reason": f"{label.title()} is the lowest-confidence area and likely unlocks the next decisions.",
        "estimated_time": "~2 hrs",
        "impact": "High — improves the biggest uncertainty in the graph",
        "node_type": weak.type.value if weak else "audience",
    }
