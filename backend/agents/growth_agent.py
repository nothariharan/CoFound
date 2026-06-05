"""Growth recommendation generator — triggered on observe signals."""

from __future__ import annotations

import json
from typing import Any

from agents.store_protocol import DEFAULT_STORE, GraphStore, ResearchTask
from llm.gemini import generate_pro


async def recommend_priority(workspace_id: str, store: GraphStore = DEFAULT_STORE, observe: dict[str, Any] | None = None) -> dict[str, str]:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    prompt = json.dumps({"workspace": workspace.model_dump(mode="json"), "observe": observe or {}}, indent=2)[:16000]
    try:
        raw = await generate_pro(prompt, system="Return JSON with action, reason, estimated_time, impact for today's highest-ROI startup task.")
        data = json.loads(raw)
    except Exception:
        data = _fallback(workspace)
    result = {
        "action": str(data.get("action") or _fallback(workspace)["action"]),
        "reason": str(data.get("reason") or _fallback(workspace)["reason"]),
        "estimated_time": str(data.get("estimated_time") or "~2 hrs"),
        "impact": str(data.get("impact") or "High — unlocks the weakest confidence node"),
    }
    if hasattr(store, "commit_research_result"):
        task = ResearchTask(workspace_id=workspace_id, task="Generate growth priority", type="growth", tools=[], priority=1)
        await getattr(store, "commit_research_result")(workspace_id, task, {"summary": result["reason"], "items": [], "sources": ["agent"], "recommendation": result}, 80)
    return result


def _fallback(workspace) -> dict[str, str]:
    weak = sorted(workspace.nodes, key=lambda n: n.confidence)[0] if workspace.nodes else None
    label = weak.type.value.replace("_", " ") if weak else "audience"
    return {
        "action": f"Run 3 focused validation conversations about {label}",
        "reason": f"{label.title()} is the lowest-confidence area and likely unlocks the next decisions.",
        "estimated_time": "~2 hrs",
        "impact": "High — improves the biggest uncertainty in the graph",
    }
