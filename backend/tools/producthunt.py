"""Product Hunt API — launch history and market timing."""

from __future__ import annotations

from typing import Any


async def search_launches(query: str, limit: int = 5) -> dict[str, Any]:
    # Product Hunt GraphQL requires app credentials; provide stable output shape.
    return {
        "tool": "producthunt",
        "query": query,
        "items": [
            {"source": "producthunt", "title": f"Launch pattern for {query}", "url": None, "snippet": "Recent launches emphasize AI automation, integrations, and fast onboarding as market timing signals."}
        ][:limit],
        "sources": ["producthunt"],
        "mock": True,
    }
