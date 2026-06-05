"""Reddit integration — pain point mining.

Uses Reddit's public JSON search when credentials/PRAW are unavailable, and falls
back to deterministic mock data for local demos.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


async def search(query: str, limit: int = 5) -> dict[str, Any]:
    return await asyncio.to_thread(_search_sync, query, limit)


def _search_sync(query: str, limit: int) -> dict[str, Any]:
    url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&limit={limit}&sort=relevance"
    req = Request(url, headers={"User-Agent": "CoFoundResearchBot/0.1"})
    try:
        with urlopen(req, timeout=20) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        children = data.get("data", {}).get("children", [])
        items = [
            {
                "source": "reddit",
                "title": c.get("data", {}).get("title"),
                "url": "https://reddit.com" + c.get("data", {}).get("permalink", ""),
                "snippet": (c.get("data", {}).get("selftext") or c.get("data", {}).get("title") or "")[:600],
                "score": c.get("data", {}).get("score", 0),
                "comments": c.get("data", {}).get("num_comments", 0),
            }
            for c in children
        ]
        if items:
            return {"tool": "reddit", "query": query, "items": items, "sources": ["reddit"]}
    except Exception:
        pass
    return _mock(query, limit)


def _mock(query: str, limit: int) -> dict[str, Any]:
    return {
        "tool": "reddit",
        "query": query,
        "items": [
            {"source": "reddit", "title": f"Users complain about manual workflow: {query}", "url": None, "snippet": "Mock Reddit result: repeated frustration with spreadsheets, reminders, and fragmented tools.", "score": 42, "comments": 18},
            {"source": "reddit", "title": f"Looking for alternatives around {query}", "url": None, "snippet": "Mock Reddit result: buyers ask for affordable automation and faster setup.", "score": 31, "comments": 11},
        ][:limit],
        "sources": ["reddit"],
        "mock": True,
    }
