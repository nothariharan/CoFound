"""GummySearch API — categorized pain point discovery."""

from __future__ import annotations

from typing import Any


async def search_pain_points(query: str, limit: int = 5) -> dict[str, Any]:
    # Public API access varies by account; keep a deterministic adapter shape for agents.
    return {
        "tool": "gummysearch",
        "query": query,
        "items": [
            {"source": "gummysearch", "title": f"Pain cluster for {query}", "url": None, "snippet": "Repeated niche communities mention manual workarounds, switching friction, and budget sensitivity."}
        ][:limit],
        "sources": ["gummysearch"],
        "mock": True,
    }
