"""Shared LLM tool-calling types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    id: str = ""


@dataclass
class LLMToolResult:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
