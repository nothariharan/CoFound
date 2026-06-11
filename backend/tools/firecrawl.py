"""Firecrawl integration — competitor landing page scraping."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


async def scrape(query_or_url: str, limit: int = 3) -> dict[str, Any]:
    key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if query_or_url.startswith(("http://", "https://")):
        if not key:
            return _mock(query_or_url, limit)
        return await asyncio.to_thread(_scrape_sync, query_or_url, key)

    if not key:
        return _mock(query_or_url, limit)

    search_results = await search(query_or_url, limit=limit)
    urls = [item.get("url") for item in search_results.get("items", []) if item.get("url")]
    if not urls:
        return search_results

    gathered = await asyncio.gather(*[asyncio.to_thread(_scrape_sync, url, key) for url in urls[:limit]])
    items: list[dict[str, Any]] = []
    for block in gathered:
        items.extend(block.get("items", []))
    return {"tool": "firecrawl", "query": query_or_url, "items": items[:limit], "sources": ["firecrawl"]}


async def search(query: str, limit: int = 5) -> dict[str, Any]:
    key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not key:
        return _mock(query, limit)
    return await asyncio.to_thread(_search_sync, query, key, limit)


def _search_sync(query: str, key: str, limit: int) -> dict[str, Any]:
    payload = {"query": query, "limit": limit}
    req = Request(
        "https://api.firecrawl.dev/v1/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=45) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        return {"tool": "firecrawl", "query": query, "items": [], "sources": ["firecrawl"], "error": str(exc)}

    raw_items = data.get("data") or []
    items = [
        {
            "source": "firecrawl",
            "title": item.get("title") or item.get("url") or query,
            "url": item.get("url"),
            "snippet": item.get("description") or item.get("markdown") or item.get("content") or "",
        }
        for item in raw_items[:limit]
        if isinstance(item, dict)
    ]
    return {"tool": "firecrawl", "query": query, "items": items, "sources": ["firecrawl"]}


def _scrape_sync(url: str, key: str) -> dict[str, Any]:
    payload = {"url": url, "formats": ["markdown"]}
    req = Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=45) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        return {"tool": "firecrawl", "query": url, "items": [], "error": str(exc), "sources": ["firecrawl"]}
    markdown = (data.get("data") or {}).get("markdown") or ""
    return {
        "tool": "firecrawl",
        "query": url,
        "items": [{"source": "firecrawl", "title": url, "url": url, "snippet": markdown[:1000]}],
        "sources": ["firecrawl"],
    }


def _mock(query: str, limit: int) -> dict[str, Any]:
    return {
        "tool": "firecrawl",
        "query": query,
        "items": [
            {
                "source": "firecrawl",
                "title": f"Firecrawl unavailable for: {query}",
                "url": None,
                "snippet": "Firecrawl API key is missing or the request failed; connect Firecrawl for live web evidence.",
            },
        ][:limit],
        "sources": ["firecrawl"],
        "fallback": True,
    }
