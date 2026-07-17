"""Reddit research through a lightweight, site-scoped web search."""

from __future__ import annotations

from typing import Any

from tools import web_search


async def search(query: str, limit: int = 5) -> dict[str, Any]:
    result = await web_search.search(f"site:reddit.com {query}", limit)
    for item in result.get("items", []):
        item["source"] = "reddit"
        item["origin"] = "reddit"
    return {**result, "tool": "reddit", "query": query, "sources": ["reddit"]}
