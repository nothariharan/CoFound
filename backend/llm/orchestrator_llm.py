"""Orchestrator LLM — Gemini with resilient fallbacks."""

from __future__ import annotations

from typing import Any

from llm.gemini import (
    GeminiError,
    GeminiToolResult,
    generate_pro_resilient,
    generate_with_tools as gemini_generate_with_tools,
)


async def generate_with_tools(
    contents: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str = "",
) -> GeminiToolResult:
    try:
        return await gemini_generate_with_tools(contents, tools, system=system)
    except GeminiError:
        from llm.gemini import _mock_tool_result

        return _mock_tool_result(contents, tools)


async def generate_text_resilient(prompt: str, system: str = "") -> str:
    return await generate_pro_resilient(prompt, system=system)
