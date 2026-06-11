"""Reddit-labeled community research.

Reddit blocks the unauthenticated JSON search endpoint from many environments,
so this module keeps the old import path while delegating to Scrapling's broad
web/community scraper.
"""

from __future__ import annotations

from typing import Any

from tools import scrapling_web


async def search(query: str, limit: int = 5) -> dict[str, Any]:
    result = await scrapling_web.search_broad(query, limit)
    return {**result, "tool": "reddit", "sources": _sources(result)}


def _sources(result: dict[str, Any]) -> list[str]:
    sources = set(result.get("sources") or [])
    sources.add("reddit")
    return sorted(sources)
