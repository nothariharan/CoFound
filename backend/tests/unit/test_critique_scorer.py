from __future__ import annotations

import asyncio
import json

from critique import scorer


def test_critique_rejects_empty_result_even_if_model_is_optimistic(monkeypatch):
    async def optimistic(prompt: str, system: str = "") -> str:
        return json.dumps({"score": 95, "verdict": "accept", "reason": "looks good", "accept": True})

    monkeypatch.setattr(scorer, "generate_flash", optimistic)

    result = asyncio.run(scorer.score({"items": [], "sources": []}, "Find evidence"))

    assert result.score < 50
    assert result.verdict == "reject"
    assert result.accept is False


def test_critique_refines_medium_quality_result(monkeypatch):
    async def optimistic(prompt: str, system: str = "") -> str:
        return json.dumps({"score": 90, "verdict": "accept", "reason": "ok", "accept": True})

    monkeypatch.setattr(scorer, "generate_flash", optimistic)
    result_payload = {
        "summary": "Some useful signal",
        "sources": ["reddit"],
        "items": [
            {"source": "reddit", "title": "pain", "url": "https://reddit.com/a"},
            {"source": "reddit", "title": "more pain", "url": "https://reddit.com/b"},
        ],
    }

    result = asyncio.run(scorer.score(result_payload, "Mine pain"))

    assert 50 <= result.score < 80
    assert result.verdict == "refine"
    assert result.accept is False


def test_critique_rejects_fallback_items_even_with_summary(monkeypatch):
    async def optimistic(prompt: str, system: str = "") -> str:
        return json.dumps({"score": 90, "verdict": "accept", "reason": "ok", "accept": True})

    monkeypatch.setattr(scorer, "generate_flash", optimistic)
    result_payload = {
        "summary": "Unavailable placeholder",
        "sources": ["reddit", "scrapling"],
        "items": [
            {
                "source": "web",
                "title": "Web scrape unavailable",
                "url": None,
                "snippet": "Web scrape failed after HTTP + stealth attempts.",
                "fallback": True,
            }
        ],
        "fallback": True,
    }

    result = asyncio.run(scorer.score(result_payload, "Mine pain"))

    assert result.score < 50
    assert result.verdict == "reject"
    assert result.accept is False


def test_critique_accepts_rich_multi_source_result(monkeypatch):
    async def model(prompt: str, system: str = "") -> str:
        return json.dumps({"score": 84, "reason": "specific evidence", "accept": True})

    monkeypatch.setattr(scorer, "generate_flash", model)
    result_payload = {
        "summary": "Specific signal",
        "sources": ["reddit", "exa"],
        "items": [
            {"source": "reddit", "title": "pain", "url": "https://reddit.com/a"},
            {"source": "exa", "title": "market", "url": "https://example.com/b"},
            {"source": "exa", "title": "competitor", "url": "https://example.com/c"},
            {"source": "reddit", "title": "pricing", "url": "https://reddit.com/d"},
        ],
    }

    result = asyncio.run(scorer.score(result_payload, "Research"))

    assert result.score >= 80
    assert result.verdict == "accept"
    assert result.accept is True
