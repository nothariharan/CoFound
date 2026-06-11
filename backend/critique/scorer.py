"""0-100 self-critique quality scorer for research results."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from llm.gemini import generate_flash


class CritiqueResult(BaseModel):
    score: int = Field(ge=0, le=100)
    verdict: str
    reason: str
    requery: str = ""
    accept: bool = False


SCORER_SYSTEM = """You are a strict research self-critique scorer.
Return ONLY JSON with: score (0-100), verdict, reason, requery, accept.
80+ accepts; 50-79 refine/requery; <50 reject as dead end.
Reward specific sources, buyer pain, competitor evidence, and actionable detail.
"""


async def score(result: dict[str, Any], task: str) -> CritiqueResult:
    heuristic = _heuristic_score(result)
    prompt = json.dumps({"task": task, "result": result, "heuristic_score": heuristic}, indent=2)[:12000]
    try:
        raw = await generate_flash(prompt, system=SCORER_SYSTEM)
        parsed = _parse_json(raw)
        final_score = _calibrate_score(int(parsed.get("score", heuristic)), heuristic)
        return CritiqueResult(
            score=max(0, min(100, final_score)),
            verdict=_verdict(final_score),
            reason=str(parsed.get("reason") or _reason(result, final_score)),
            requery=str(parsed.get("requery") or ""),
            accept=bool(parsed.get("accept", final_score >= 80)) and final_score >= 80,
        )
    except Exception:
        return CritiqueResult(score=heuristic, verdict=_verdict(heuristic), reason=_reason(result, heuristic), requery=_requery(task), accept=heuristic >= 80)


def _calibrate_score(model_score: int, heuristic: int) -> int:
    """Prevent an over-optimistic LLM/mock from accepting evidence-poor results."""

    if heuristic < 50:
        return min(model_score, 49)
    if heuristic < 75:
        return min(model_score, 79)
    return max(heuristic, min(100, model_score))


def _heuristic_score(result: dict[str, Any]) -> int:
    items = result.get("items") or []
    real_items = [item for item in items if isinstance(item, dict) and item.get("url") and not item.get("fallback")]
    fallback_items = [item for item in items if isinstance(item, dict) and (item.get("fallback") or not item.get("url"))]
    score = 25
    score += min(35, len(real_items) * 10)
    if result.get("summary"):
        score += 15
    if len(set(result.get("sources") or [])) >= 2:
        score += 10
    if len(real_items) >= 2:
        score += 10
    if result.get("fallback") or result.get("error"):
        score -= 25
    if fallback_items and not real_items:
        score -= 20
    return max(0, min(100, score))


def _verdict(value: int) -> str:
    if value >= 80:
        return "accept"
    if value >= 50:
        return "refine"
    return "reject"


def _reason(result: dict[str, Any], value: int) -> str:
    if value >= 80:
        return "Specific enough with multiple evidence items."
    if value >= 50:
        return "Useful signal but too broad — refining query."
    return "Too little evidence or tool failure."


def _requery(task: str) -> str:
    return f"{task} specific customer pain evidence pricing competitor"


def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
        if match:
            return json.loads(match.group(1))
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise
