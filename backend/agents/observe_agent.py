"""posthog funnel monitor — detects conversion drops"""
from __future__ import annotations

from typing import Any

from agents.growth_agent import recommend_priority
from agents.store_protocol import GraphStore, ResearchTask
from mdb_mcp.agent_store import get_agent_store
from sse.feed import feed
from tools.posthog_client import get_funnel


async def observe_funnel(workspace_id: str, store: GraphStore | None = None, project_id: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    store = store or get_agent_store()
    data = await get_funnel(project_id=project_id, api_key=api_key)
    drops = _detect_drops(data)
    summary = _summary(drops)
    if data.get("fallback"):
        summary = f"{data.get('label', 'PostHog not connected; fallback funnel used')}. {summary}"
    result = {"funnel": data.get("funnel") or data.get("data"), "drops": drops, "sources": ["posthog"], "summary": summary, "fallback": bool(data.get("fallback"))}
    if hasattr(store, "commit_research_result"):
        score = 85 if drops else 75
        task = ResearchTask(workspace_id=workspace_id, task="Monitor PostHog funnel", type="observe", tools=["posthog"], priority=1)
        await getattr(store, "commit_research_result")(workspace_id, task, result, score)
    if drops:
        result["growth_recommendation"] = await recommend_priority(workspace_id, store=store, observe=result)
    await feed.publish(
        workspace_id,
        {
            "text": f"[Observe Agent] {summary}",
            "type": "info",
        },
    )
    return result


def _detect_drops(data: dict[str, Any]) -> list[dict[str, Any]]:
    drops: list[dict[str, Any]] = []
    for step in data.get("funnel", []) or []:
        try:
            current = float(step.get("conversion", 0) or 0)
            previous = float(step.get("previous_conversion", current) or current)
        except (TypeError, ValueError):
            continue
        delta_pp = (current - previous) * 100
        if delta_pp <= -5:
            drops.append({"step": step.get("step"), "delta_pp": round(delta_pp, 2), "current": current, "previous": previous})
    return drops


def _summary(drops: list[dict[str, Any]]) -> str:
    if not drops:
        return "No >5pp conversion drop detected."
    first = drops[0]
    return f"Detected {len(drops)} funnel drop(s); largest visible issue at {first.get('step')} ({first.get('delta_pp')}pp)."
