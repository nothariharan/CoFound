"""Conversational orchestrator — tool-calling chat loop."""

from __future__ import annotations

import json
from typing import Any

from agents.orchestrator_tools import TOOL_DECLARATIONS, execute_tool, tool_summary
from agents.store_protocol import GraphStore
from mdb_mcp.agent_store import get_agent_store
from llm.gemini import generate_pro, generate_with_tools

SYSTEM = """You are the CoFounder Orchestrator — the single AI co-founder that coordinates specialist sub-agents on a startup knowledge graph.

You can call tools to:
- Read workspace status and today's priority
- Start research on nodes, spawn sessions, hand off priorities, run custom tasks, pivot the idea, or export

When the user asks you to DO something, call the appropriate tool — do not just tell them what buttons to click.
When they ask for status or updates, call get_workspace_summary first.
For UI requests like "show me audience" or "open settings", use request_ui_action.

After tool results, respond naturally in 1-3 concise sentences for voice (speaking_text).
Always confirm what you started and that activity will appear in the live feed.

Return your final answer as JSON with keys:
- reply: full text response for the chat UI
- speaking_text: shorter version for text-to-speech (max 2 sentences)
"""

MAX_TOOL_ROUNDS = 3


async def orchestrator_chat(
    workspace_id: str,
    message: str,
    history: list[dict[str, str]] | None = None,
    store: GraphStore | None = None,
) -> dict[str, Any]:
    store = store or get_agent_store()
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    actions_taken: list[dict[str, str]] = []
    ui_actions: list[dict[str, Any]] = []

    graph_snapshot = json.dumps(
        {
            "workspace_name": workspace.workspace_name,
            "nodes": [
                {
                    "type": n.type.value,
                    "title": n.title,
                    "confidence": n.confidence,
                    "status": n.status.value,
                    "active_agents": n.active_agents,
                }
                for n in workspace.nodes
            ],
        },
        indent=2,
    )[:8000]

    contents: list[dict[str, Any]] = []
    for turn in (history or [])[-10:]:
        role = "user" if turn.get("role") == "user" else "model"
        text = str(turn.get("text") or "").strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    user_prompt = f"""Current graph snapshot:
{graph_snapshot}

User message: {message.strip()}

Use tools if needed, then respond with JSON: {{"reply": "...", "speaking_text": "..."}}"""
    contents.append({"role": "user", "parts": [{"text": user_prompt}]})

    final_text: str | None = None
    for _ in range(MAX_TOOL_ROUNDS):
        result = await generate_with_tools(contents, TOOL_DECLARATIONS, system=SYSTEM)
        if result.tool_calls:
            model_parts: list[dict[str, Any]] = []
            response_parts: list[dict[str, Any]] = []
            for call in result.tool_calls:
                model_parts.append({"functionCall": {"name": call.name, "args": call.args}})
                try:
                    tool_result = await execute_tool(call.name, call.args, workspace_id, store=store)
                except Exception as exc:
                    tool_result = {"error": str(exc)}
                actions_taken.append({"tool": call.name, "summary": tool_summary(call.name, tool_result)})
                ui_action = tool_result.get("ui_action")
                if ui_action:
                    ui_actions.append(ui_action)
                response_parts.append(
                    {
                        "functionResponse": {
                            "name": call.name,
                            "response": tool_result,
                        }
                    }
                )
            contents.append({"role": "model", "parts": model_parts})
            contents.append({"role": "user", "parts": response_parts})
            continue

        final_text = result.text
        break

    if not final_text:
        final_text = await generate_pro(
            f"Summarize what happened for the user. Actions: {json.dumps(actions_taken)}. User asked: {message}",
            system="Reply in JSON with reply and speaking_text keys. Be concise.",
        )

    parsed = _parse_response(final_text, message, actions_taken)
    parsed["actions_taken"] = actions_taken
    parsed["ui_actions"] = ui_actions
    return parsed


def _parse_response(raw: str, message: str, actions_taken: list[dict[str, str]]) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
        reply = str(data.get("reply") or data.get("brief") or text).strip()
        speaking = str(data.get("speaking_text") or reply).strip()
        return {"reply": reply, "speaking_text": speaking}
    except Exception:
        pass

    if actions_taken:
        summaries = "; ".join(item["summary"] for item in actions_taken)
        reply = f"{text}\n\nActions: {summaries}" if text else f"Done. {summaries}"
    else:
        reply = text or "I'm here — ask for a status update or tell me what to research next."

    speaking = reply.split("\n")[0][:240]
    return {"reply": reply, "speaking_text": speaking}
