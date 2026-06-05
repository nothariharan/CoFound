"""Exa.ai integration — neural semantic web search."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


async def search(query: str, num_results: int = 5) -> dict[str, Any]:
    key = os.getenv("EXA_API_KEY", "").strip()
    if not key:
        return _mock(query, num_results)
    return await asyncio.to_thread(_search_sync, query, num_results, key)


def _search_sync(query: str, num_results: int, key: str) -> dict[str, Any]:
    payload = {"query": query, "numResults": num_results, "contents": {"text": True}}
    req = Request(
        "https://api.exa.ai/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": key},
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        return {"tool": "exa", "query": query, "items": [], "error": str(exc), "sources": ["exa"]}
    items = [
        {
            "source": "exa",
            "title": r.get("title") or r.get("url"),
            "url": r.get("url"),
            "snippet": (r.get("text") or "")[:600],
        }
        for r in data.get("results", [])
    ]
    return {"tool": "exa", "query": query, "items": items, "sources": ["exa"]}


def _mock(query: str, num_results: int) -> dict[str, Any]:
    return {
        "tool": "exa",
        "query": query,
        "items": [
            {"source": "exa", "title": f"Market signal for {query}", "url": None, "snippet": "Mock Exa result: recurring demand, competitor activity, and budget-holder urgency detected."},
            {"source": "exa", "title": f"Competitor landscape for {query}", "url": None, "snippet": "Mock Exa result: incumbents solve adjacent workflow but leave onboarding and niche automation gaps."},
        ][:num_results],
        "sources": ["exa"],
        "mock": True,
    }
