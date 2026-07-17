"""conversational orchestrator — tool calling chat loop"""
from __future__ import annotations

import json
import uuid
from typing import Any

from agents.orchestrator_tools import TOOL_DECLARATIONS, execute_tool, infer_tool_calls_from_message, tool_summary
from agents.store_protocol import GraphStore, get_store
from llm.gemini import GeminiError, GeminiToolCall, GeminiToolResult
from llm.orchestrator_llm import generate_text_resilient, generate_with_tools

SYSTEM = """You are the CoFounder Orchestrator — the single AI co-founder that coordinates specialist sub-agents on a startup knowledge graph.

You can call tools to:
- Read workspace status and today's priority
- Start research on nodes, spawn sessions, hand off priorities, run custom tasks, pivot the idea, or export

When the user asks you to DO something, call the appropriate tool — do not just tell them what buttons to click.
When they ask for status or updates, call get_workspace_summary first.
For UI requests like "show me audience" or "open settings", use request_ui_action.
For research requests (especially multiple topics, current solutions, or custom questions), use spawn_research_agents — it creates new nodes on the graph and runs parallel sub-agents.
Do NOT call start_node_research on a node that already has active_agents in the graph snapshot.
Call each tool at most once per user message.

After tool results, respond naturally in 1-3 concise sentences for voice (speaking_text).
Always confirm what you started and that activity will appear in the live feed.

Return your final answer as JSON with keys:
- reply: full text response for the chat UI
- speaking_text: shorter version for text-to-speech (max 2 sentences)
"""

MAX_TOOL_ROUNDS = 1


def _dedupe_actions(actions: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in actions:
        key = f"{item.get('tool')}::{item.get('summary')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


async def orchestrator_chat(
    workspace_id: str,
    message: str,
    history: list[dict[str, str]] | None = None,
    store: GraphStore | None = None,
) -> dict[str, Any]:
    store = store or get_store()
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")

    actions_taken: list[dict[str, str]] = []
    ui_actions: list[dict[str, Any]] = []

    preflight = infer_tool_calls_from_message(message)
    if len(preflight) == 1 and preflight[0].name == "spawn_research_agents":
        tool_args = {**preflight[0].args, "user_message": message}
        tool_result = await execute_tool("spawn_research_agents", tool_args, workspace_id, store=store)
        actions_taken.append({"tool": "spawn_research_agents", "summary": tool_summary("spawn_research_agents", tool_result)})
        parsed = _reply_from_actions(message, workspace, actions_taken, ui_actions)
        parsed["actions_taken"] = actions_taken
        parsed["ui_actions"] = ui_actions
        return parsed

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
        try:
            result = await generate_with_tools(contents, TOOL_DECLARATIONS, system=SYSTEM)
        except GeminiError:
            result = await _rule_based_tool_result(message)
        if result.tool_calls:
            model_parts: list[dict[str, Any]] = []
            response_parts: list[dict[str, Any]] = []
            seen_calls: set[str] = set()
            for call in result.tool_calls:
                call_key = f"{call.name}::{json.dumps(call.args, sort_keys=True)}"
                if call_key in seen_calls:
                    continue
                seen_calls.add(call_key)
                call_id = call.id or uuid.uuid4().hex
                model_parts.append({"functionCall": {"name": call.name, "args": call.args, "id": call_id}})
                tool_args = dict(call.args)
                if call.name == "spawn_research_agents" and not str(tool_args.get("user_message") or "").strip():
                    tool_args["user_message"] = message
                try:
                    tool_result = await execute_tool(call.name, tool_args, workspace_id, store=store)
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
                            "id": call_id,
                        }
                    }
                )
            if model_parts:
                contents.append({"role": "model", "parts": model_parts})
                contents.append({"role": "user", "parts": response_parts})
            actions_taken[:] = _dedupe_actions(actions_taken)
            parsed = _reply_from_actions(message, workspace, actions_taken, ui_actions)
            parsed["actions_taken"] = actions_taken
            parsed["ui_actions"] = ui_actions
            return parsed

        final_text = result.text
        break

    if not final_text:
        if actions_taken:
            actions_taken[:] = _dedupe_actions(actions_taken)
            parsed = _reply_from_actions(message, workspace, actions_taken, ui_actions)
            parsed["actions_taken"] = actions_taken
            parsed["ui_actions"] = ui_actions
            return parsed
        final_text = await generate_text_resilient(
            f"Summarize what happened for the user. Actions: {json.dumps(actions_taken)}. User asked: {message}",
            system="Reply in JSON with reply and speaking_text keys. Be concise.",
        )

    parsed = _parse_response(final_text, message, actions_taken)
    actions_taken[:] = _dedupe_actions(actions_taken)
    parsed["actions_taken"] = actions_taken
    parsed["ui_actions"] = ui_actions
    return parsed


async def _rule_based_tool_result(message: str) -> GeminiToolResult:
    calls = infer_tool_calls_from_message(message)
    return GeminiToolResult(text=None, tool_calls=[GeminiToolCall(name=c.name, args=c.args, id=c.id) for c in calls])


def _reply_from_actions(message, workspace, actions_taken, ui_actions) -> dict[str, Any]:
    if not actions_taken:
        weak = sorted(workspace.nodes, key=lambda n: n.confidence)
        target = next((n for n in weak if n.type.value != "core_idea" and n.status.value != "locked"), None)
        hint = f" Try approving research on {target.title} next." if target else ""
        return {
            "reply": f"I'm ready to help with {workspace.workspace_name}.{hint} Ask for a status update or tell me what to research.",
            "speaking_text": f"I'm ready to help with {workspace.workspace_name}.",
        }

    started = [a for a in actions_taken if a["tool"] == "start_node_research" and "Started research" in a["summary"]]
    spawned = [a for a in actions_taken if a["tool"] == "spawn_research_agents"]
    already_running = [a for a in actions_taken if "already running" in a["summary"].lower()]
    locked = [a for a in actions_taken if "locked" in a["summary"].lower()]

    if spawned:
        summary = spawned[0]["summary"]
        reply = f"{summary}. New research nodes are on your graph — watch the Activity tab for live updates."
        return {"reply": reply, "speaking_text": "Research agents are running. Check the activity feed."}

    if started:
        node = started[0]["summary"].replace("Started research on ", "")
        reply = f"Started research on {node}. Watch the Activity tab for live updates."
        return {"reply": reply, "speaking_text": f"Research is running on {node}. Check the activity feed."}

    if already_running:
        node = already_running[0]["summary"]
        idle = next(
            (
                n
                for n in workspace.nodes
                if not n.active_agents and n.status.value != "locked" and n.type.value != "core_idea"
            ),
            None,
        )
        suggestion = f" Try research on {idle.title} instead." if idle else " Check the Activity tab for live progress."
        reply = f"{node}.{suggestion}"
        return {"reply": reply, "speaking_text": "That research is already running. Check the activity feed."}

    if locked:
        reply = locked[0]["summary"] + " Complete prerequisite nodes first or pick an unlocked node."
        return {"reply": reply, "speaking_text": "That node is still locked."}

    summaries = "; ".join(item["summary"] for item in actions_taken)
    speaking = summaries.split(".")[0][:220]
    if any(item["tool"] == "handoff_priority" for item in actions_taken):
        speaking = "I handed off today's priority. Agents are working now."
    elif any(item["tool"] == "get_workspace_summary" for item in actions_taken):
        active = sum(1 for n in workspace.nodes if n.active_agents)
        speaking = f"{workspace.workspace_name} has {len(workspace.nodes)} nodes and {active} active agent(s)."
    return {"reply": summaries, "speaking_text": speaking}


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
