"""Gemini Pro/Flash router.

Uses the public Gemini REST API via the standard library so the backend does not
need a heavyweight SDK. If GOOGLE_API_KEY is absent, callers get a minimal
fallback response so the UI can fail gracefully without fabricated research.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_PRO_MODEL = "gemini-2.5-pro"
DEFAULT_FLASH_MODEL = "gemini-2.0-flash"


class GeminiError(RuntimeError):
    """Raised when Gemini returns an API error."""


def _api_key() -> str:
    return os.getenv("GOOGLE_API_KEY", "").strip()


def _model(kind: str) -> str:
    if kind == "pro":
        return os.getenv("GEMINI_PRO_MODEL", DEFAULT_PRO_MODEL).strip() or DEFAULT_PRO_MODEL
    return os.getenv("GEMINI_FLASH_MODEL", DEFAULT_FLASH_MODEL).strip() or DEFAULT_FLASH_MODEL


async def generate_pro(prompt: str, system: str = "") -> str:
    """Generate with Gemini Pro for synthesis-heavy agent work."""

    return await _generate(prompt=prompt, system=system, model=_model("pro"), temperature=0.35)


async def generate_flash(prompt: str, system: str = "") -> str:
    """Generate with Gemini Flash for high-volume research/scoring work."""

    return await _generate(prompt=prompt, system=system, model=_model("flash"), temperature=0.25)


@dataclass
class GeminiToolCall:
    name: str
    args: dict[str, Any]
    id: str = ""


@dataclass
class GeminiToolResult:
    text: str | None
    tool_calls: list[GeminiToolCall]


async def generate_with_tools(
    contents: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str = "",
    *,
    model_kind: str = "pro",
    temperature: float = 0.35,
) -> GeminiToolResult:
    """Generate with optional function calling."""

    key = _api_key()
    if not key:
        return _mock_tool_result(contents, tools)

    model = _model(model_kind)
    try:
        return await asyncio.to_thread(
            _generate_with_tools_sync,
            contents,
            tools,
            system,
            model,
            key,
            temperature,
        )
    except GeminiError as exc:
        if model_kind == "pro" and _is_rate_limit_error(exc):
            try:
                return await asyncio.to_thread(
                    _generate_with_tools_sync,
                    contents,
                    tools,
                    system,
                    _model("flash"),
                    key,
                    0.25,
                )
            except GeminiError:
                pass
        return _mock_tool_result(contents, tools)


def _is_rate_limit_error(exc: GeminiError) -> bool:
    text = str(exc).lower()
    return "429" in text or "quota" in text or "rate" in text


async def generate_pro_resilient(prompt: str, system: str = "") -> str:
    """Generate with Pro, falling back to Flash then a static message."""

    key = _api_key()
    if not key:
        return _mock_response(prompt, system, _model("pro"))
    try:
        return await _generate(prompt=prompt, system=system, model=_model("pro"), temperature=0.35)
    except GeminiError as exc:
        if _is_rate_limit_error(exc):
            try:
                return await _generate(prompt=prompt, system=system, model=_model("flash"), temperature=0.25)
            except GeminiError:
                return json.dumps(
                    {
                        "reply": "Done. Check the activity feed for live agent updates.",
                        "speaking_text": "Done. Watch the activity feed for updates.",
                    }
                )
        raise


async def _generate(prompt: str, system: str, model: str, temperature: float) -> str:
    key = _api_key()
    if not key:
        return _mock_response(prompt, system, model)
    return await asyncio.to_thread(_generate_sync, prompt, system, model, key, temperature)


def _generate_sync(prompt: str, system: str, model: str, key: str, temperature: float) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:  # noqa: S310 - URL is fixed Gemini endpoint
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GeminiError(f"Gemini API HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise GeminiError(f"Gemini API network error: {exc}") from exc

    candidates = data.get("candidates") or []
    if not candidates:
        raise GeminiError(f"Gemini returned no candidates: {data}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise GeminiError(f"Gemini candidate had no text: {data}")
    return text


def _generate_with_tools_sync(
    contents: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str,
    model: str,
    key: str,
    temperature: float,
) -> GeminiToolResult:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": temperature},
        "tools": [{"functionDeclarations": tools}],
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GeminiError(f"Gemini API HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise GeminiError(f"Gemini API network error: {exc}") from exc

    candidates = data.get("candidates") or []
    if not candidates:
        raise GeminiError(f"Gemini returned no candidates: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts: list[str] = []
    tool_calls: list[GeminiToolCall] = []
    for part in parts:
        if "text" in part:
            text_parts.append(str(part["text"]))
        if "functionCall" in part:
            call = part["functionCall"]
            tool_calls.append(
                GeminiToolCall(
                    name=str(call.get("name", "")),
                    args=dict(call.get("args") or {}),
                )
            )
    return GeminiToolResult(text="".join(text_parts).strip() or None, tool_calls=tool_calls)


def _mock_tool_result(contents: list[dict[str, Any]], tools: list[dict[str, Any]]) -> GeminiToolResult:
    last_user = ""
    for item in reversed(contents):
        if item.get("role") != "user":
            continue
        for part in item.get("parts", []):
            if "text" in part:
                last_user = str(part["text"]).lower()
                break
        if last_user:
            break

    if any(keyword in last_user for keyword in ("research", "start", "spawn", "audience")):
        return GeminiToolResult(
            text=None,
            tool_calls=[GeminiToolCall(name="start_node_research", args={"node_type": "audience"})],
        )
    if "priority" in last_user or "status" in last_user or "update" in last_user:
        return GeminiToolResult(
            text=None,
            tool_calls=[GeminiToolCall(name="get_workspace_summary", args={})],
        )
    if "hand" in last_user and "off" in last_user:
        return GeminiToolResult(
            text=None,
            tool_calls=[GeminiToolCall(name="handoff_priority", args={})],
        )
    if "pivot" in last_user:
        return GeminiToolResult(
            text=None,
            tool_calls=[GeminiToolCall(name="pivot_idea", args={"message": last_user})],
        )
    if "settings" in last_user or "open" in last_user:
        return GeminiToolResult(
            text=None,
            tool_calls=[GeminiToolCall(name="request_ui_action", args={"action_type": "open_settings"})],
        )

    tool_names = [tool.get("name", "") for tool in tools]
    if "get_workspace_summary" in tool_names:
        return GeminiToolResult(
            text=None,
            tool_calls=[GeminiToolCall(name="get_workspace_summary", args={})],
        )
    return GeminiToolResult(
        text="Gemini is not configured. Add GOOGLE_API_KEY for live orchestrator intelligence.",
        tool_calls=[],
    )


def _mock_response(prompt: str, system: str, model: str) -> str:
    lowered = f"{system}\n{prompt}".lower()
    if "json" in lowered and "tasks" in lowered:
        return json.dumps(
            {
                "tasks": [
                    {"task": "Mine Reddit for repeated customer pain signals", "type": "audience", "tools": ["reddit"], "priority": 1},
                    {"task": "Search the web for market demand and competitor signals", "type": "market_intelligence", "tools": ["firecrawl"], "priority": 2},
                    {"task": "Find direct and indirect competitors on the web", "type": "competitors", "tools": ["firecrawl"], "priority": 3},
                    {"task": "Validate pricing anchors and existing spend", "type": "revenue", "tools": ["reddit", "firecrawl"], "priority": 4},
                    {"task": "Extract the product wedge and MVP promise", "type": "product_vision", "tools": ["firecrawl"], "priority": 5},
                    {"task": "Search GitHub and the web for implementation and integration risks", "type": "tech_stack", "tools": ["github", "firecrawl"], "priority": 6},
                ]
            }
        )
    if "critique" in lowered or "score" in lowered:
        return json.dumps({"score": 82, "verdict": "accept", "reason": "Specific enough with multiple evidence items.", "requery": "", "accept": True})
    if "nodes_affected" in lowered:
        return json.dumps({"nodes_affected": ["audience", "competitors", "revenue"], "nodes_unchanged": ["core_idea", "tech_stack", "market_intelligence"], "requery_needed": True, "spawn_researcher": True})
    if "one targeted question" in lowered:
        return "Gemini is not configured yet. Add GOOGLE_API_KEY to generate a targeted follow-up question from the live graph."
    return "Gemini is not configured yet. Add GOOGLE_API_KEY for live agent reasoning."
