"""synthesis + targeted question agent — post research dialogue"""
from __future__ import annotations

import json

from agents.store_protocol import GraphStore
from mdb_mcp.agent_store import get_agent_store
from llm.gemini import generate_pro

SYSTEM = """Read the startup graph and synthesize a concise brief.
Return JSON with keys: brief, question. The question must be exactly one targeted question.
"""


async def synthesize_dialogue(workspace_id: str, store: GraphStore | None = None) -> dict[str, str]:
    store = store or get_agent_store()
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    prompt = json.dumps(workspace.model_dump(mode="json"), indent=2)[:16000]
    raw = await generate_pro(prompt, system=SYSTEM)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"brief": raw, "question": _fallback_question(workspace)}
    question = str(data.get("question") or _fallback_question(workspace)).strip().split("\n")[0]
    # ensure exactly one question mark in response field
    if "?" in question:
        question = question.split("?")[0].strip() + "?"
    else:
        question = question.rstrip(".") + "?"
    return {"brief": str(data.get("brief") or "Graph synthesized."), "question": question}


def _fallback_question(workspace) -> str:
    weak = sorted(workspace.nodes, key=lambda n: n.confidence)[0] if workspace.nodes else None
    if weak:
        return f"What evidence would most increase confidence in {weak.type.value.replace('_', ' ')}?"
    return "Who is the first customer segment you can interview this week?"
