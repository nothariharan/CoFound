"""Orchestrator LLM router — optional remote provider when credentials are present, else Gemini."""

from __future__ import annotations

from typing import Any

from llm import _converse
from llm.gemini import (
    GeminiError,
    GeminiToolCall,
    GeminiToolResult,
    generate_pro_resilient,
    generate_with_tools as gemini_generate_with_tools,
)


def remote_enabled() -> bool:
    return _converse.is_configured()


async def generate_with_tools(
    contents: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str = "",
) -> GeminiToolResult:
    if remote_enabled():
        try:
            remote = await _converse.generate_with_tools(contents, tools, system=system)
            return GeminiToolResult(
                text=remote.text,
                tool_calls=[
                    GeminiToolCall(name=call.name, args=call.args, id=call.id) for call in remote.tool_calls
                ],
            )
        except _converse.ConverseError:
            pass
    try:
        return await gemini_generate_with_tools(contents, tools, system=system)
    except GeminiError:
        from llm.gemini import _mock_tool_result

        return _mock_tool_result(contents, tools)


async def generate_text_resilient(prompt: str, system: str = "") -> str:
    if remote_enabled():
        try:
            text = await _converse.generate_text(prompt, system=system)
            if text.strip():
                return text
        except _converse.ConverseError:
            pass
    return await generate_pro_resilient(prompt, system=system)
