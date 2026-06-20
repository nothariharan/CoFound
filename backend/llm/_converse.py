"""remote orchestrator llm via converse api (credentials from env only)"""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from typing import Any

from llm.types import LLMToolResult, ToolCall

DEFAULT_MODEL = "amazon.nova-lite-v1:0"


class ConverseError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(os.getenv("AWS_ACCESS_KEY_ID", "").strip() and os.getenv("AWS_SECRET_ACCESS_KEY", "").strip())


def _region() -> str:
    return os.getenv("AWS_REGION", os.getenv("ORCHESTRATOR_REGION", "us-east-1")).strip() or "us-east-1"


def _model_id() -> str:
    return os.getenv("ORCHESTRATOR_MODEL_ID", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _client():
    import boto3

    return boto3.client(
        "bedrock-runtime",
        region_name=_region(),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "").strip(),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "").strip(),
    )


def _to_tool_config(tools: list[dict[str, Any]]) -> dict[str, Any]:
    specs = []
    for tool in tools:
        params = dict(tool.get("parameters") or {"type": "object", "properties": {}})
        specs.append(
            {
                "toolSpec": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": {"json": params},
                }
            }
        )
    return {"tools": specs}


def _contents_to_messages(contents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for item in contents:
        role = "user" if item.get("role") == "user" else "assistant"
        blocks: list[dict[str, Any]] = []
        for part in item.get("parts", []):
            if "text" in part:
                blocks.append({"text": str(part["text"])})
                continue
            if "functionCall" in part:
                call = part["functionCall"]
                blocks.append(
                    {
                        "toolUse": {
                            "toolUseId": str(call.get("id") or uuid.uuid4()),
                            "name": str(call.get("name", "")),
                            "input": dict(call.get("args") or {}),
                        }
                    }
                )
                continue
            if "functionResponse" in part:
                response = part["functionResponse"]
                payload = response.get("response", response)
                blocks.append(
                    {
                        "toolResult": {
                            "toolUseId": str(response.get("id") or uuid.uuid4()),
                            "content": [{"json": payload}],
                        }
                    }
                )
        if blocks:
            messages.append({"role": role, "content": blocks})
    return messages


def _parse_output(data: dict[str, Any]) -> LLMToolResult:
    message = (data.get("output") or {}).get("message") or {}
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for block in message.get("content") or []:
        if "text" in block:
            text_parts.append(str(block["text"]))
        if "toolUse" in block:
            use = block["toolUse"]
            tool_calls.append(
                ToolCall(
                    id=str(use.get("toolUseId") or uuid.uuid4()),
                    name=str(use.get("name", "")),
                    args=dict(use.get("input") or {}),
                )
            )
    return LLMToolResult(text=_clean_text("".join(text_parts).strip()) or None, tool_calls=tool_calls)


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    return cleaned


def _converse_sync(contents: list[dict[str, Any]], tools: list[dict[str, Any]], system: str) -> LLMToolResult:
    messages = _contents_to_messages(contents)
    if not messages:
        raise ConverseError("No messages to send")

    kwargs: dict[str, Any] = {
        "modelId": _model_id(),
        "messages": messages,
        "inferenceConfig": {"maxTokens": 1024, "temperature": 0.3},
    }
    if system:
        kwargs["system"] = [{"text": system}]
    if tools:
        kwargs["toolConfig"] = _to_tool_config(tools)

    try:
        data = _client().converse(**kwargs)
    except Exception as exc:
        raise ConverseError(str(exc)) from exc
    return _parse_output(data)


def _text_sync(prompt: str, system: str) -> str:
    kwargs: dict[str, Any] = {
        "modelId": _model_id(),
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 768, "temperature": 0.3},
    }
    if system:
        kwargs["system"] = [{"text": system}]
    try:
        data = _client().converse(**kwargs)
    except Exception as exc:
        raise ConverseError(str(exc)) from exc
    result = _parse_output(data)
    return _clean_text(result.text or "")


async def generate_with_tools(
    contents: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str = "",
) -> LLMToolResult:
    if not is_configured():
        raise ConverseError("Remote orchestrator credentials are not configured")
    return await asyncio.to_thread(_converse_sync, contents, tools, system)


async def generate_text(prompt: str, system: str = "") -> str:
    if not is_configured():
        raise ConverseError("Remote orchestrator credentials are not configured")
    return await asyncio.to_thread(_text_sync, prompt, system)
