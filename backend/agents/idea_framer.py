"""Initial idea framing for user-approved workflows."""

from __future__ import annotations

import json
import re
from typing import Any

from llm.gemini import generate_pro

SYSTEM = """Frame a raw startup idea before research starts.
Return ONLY JSON: workspace_name, core_title, problem, solution, one_liner, confidence.
workspace_name: a concise 2-4 word product name that captures WHAT is being built
  (e.g. "PassportRenewal OS", "Fleet Tracker SaaS") - NOT the user's phrasing.
core_title: short label for the core idea node.
Do not claim external validation or research evidence.
"""


async def frame_idea(idea: str) -> dict[str, Any]:
    raw_idea = idea.strip()
    fallback = _fallback(raw_idea)
    try:
        data = _parse_json(await generate_pro(raw_idea[:4000], system=SYSTEM))
    except Exception:
        return fallback

    workspace_name = _clean_title(data.get("workspace_name")) or fallback["workspace_name"]
    core_title = _clean_title(data.get("core_title")) or "Core Idea"
    one_liner = _clean_sentence(data.get("one_liner")) or fallback["one_liner"]
    problem = _clean_sentence(data.get("problem")) or raw_idea
    solution = _clean_sentence(data.get("solution")) or ""
    confidence = _coerce_confidence(data.get("confidence"), fallback["confidence"])

    return {
        "workspace_name": workspace_name,
        "core_title": core_title,
        "problem": problem,
        "solution": solution,
        "one_liner": one_liner,
        "confidence": confidence,
    }


def _fallback(idea: str) -> dict[str, Any]:
    title = _title_from_idea(idea) or "Untitled Startup"
    return {
        "workspace_name": title,
        "core_title": "Core Idea",
        "problem": idea,
        "solution": "",
        "one_liner": idea[:160] or title,
        "confidence": 70,
    }


def _parse_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
        if match:
            value = json.loads(match.group(1))
        else:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise
            value = json.loads(text[start : end + 1])
    return value if isinstance(value, dict) else {}


def _clean_title(value: Any) -> str:
    text = str(value or "").strip().strip("\"'")
    return re.sub(r"\s+", " ", text)[:80]


def _clean_sentence(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"\s+", " ", text)[:500]


def _coerce_confidence(value: Any, fallback: int) -> int:
    try:
        return max(70, min(85, int(value)))
    except (TypeError, ValueError):
        return fallback


def _title_from_idea(idea: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", idea)
    stop = {
        "for",
        "with",
        "that",
        "and",
        "the",
        "a",
        "an",
        "to",
        "of",
        "in",
        "i",
        "want",
        "build",
        "create",
        "make",
        "making",
        "manage",
        "managing",
        "need",
        "we",
        "our",
        "my",
        "us",
        "its",
        "all",
        "just",
        "basically",
        "whole",
        "process",
        "it",
        "this",
        "is",
        "am",
        "are",
        "be",
        "been",
        "can",
        "will",
        "would",
        "could",
        "should",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "get",
        "got",
        "use",
        "using",
        "saas",
        "app",
        "platform",
    }
    picked = [word for word in words if word.lower() not in stop][:5]
    return " ".join(word.capitalize() for word in picked)
