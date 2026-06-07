"""Gemini Pro/Flash router.

Uses the public Gemini REST API via the standard library so the backend does not
need a heavyweight SDK. If GOOGLE_API_KEY is absent, callers get a deterministic
mock response, which keeps local demos/tests working without secrets.
"""

from __future__ import annotations

import asyncio
import json
import os
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


def _mock_response(prompt: str, system: str, model: str) -> str:
    lowered = f"{system}\n{prompt}".lower()
    if "json" in lowered and "tasks" in lowered:
        return json.dumps(
            {
                "tasks": [
                    {"task": "Find painful customer segments and repeated pain points", "type": "audience", "tools": ["reddit", "exa", "vector_search"], "priority": 1},
                    {"task": "Map market size, trends, and urgency signals", "type": "market_intelligence", "tools": ["exa", "firecrawl", "vector_search"], "priority": 2},
                    {"task": "Identify direct and indirect competitors", "type": "competitors", "tools": ["exa", "firecrawl"], "priority": 3},
                    {"task": "Validate monetization and existing spend", "type": "revenue", "tools": ["reddit", "exa"], "priority": 4},
                    {"task": "Extract minimum lovable product and feature wedge", "type": "product_vision", "tools": ["firecrawl", "exa", "vector_search"], "priority": 5},
                    {"task": "Assess technical stack, integrations, and moat risk", "type": "tech_stack", "tools": ["github", "exa"], "priority": 6},
                ]
            }
        )
    if "critique" in lowered or "score" in lowered:
        return json.dumps({"score": 82, "verdict": "accept", "reason": "Specific enough with multiple evidence items.", "requery": "", "accept": True})
    if "nodes_affected" in lowered:
        return json.dumps({"nodes_affected": ["audience", "competitors", "revenue"], "nodes_unchanged": ["core_idea", "tech_stack", "market_intelligence"], "requery_needed": True, "spawn_researcher": True})
    if "one targeted question" in lowered:
        return "What is the single customer segment with the highest urgency and easiest first distribution channel?"
    return "Mock Gemini response: GOOGLE_API_KEY is not configured, so this deterministic local response was used."
