"""Firecrawl integration — competitor landing page scraping."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from tools import exa_search


async def scrape(query_or_url: str, limit: int = 3) -> dict[str, Any]:
    key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if query_or_url.startswith(("http://", "https://")):
        if not key:
            return _mock(query_or_url, limit)
        return await asyncio.to_thread(_scrape_sync, query_or_url, key)

    if not key:
        return _mock(query_or_url, limit)

    exa = await exa_search.search(query_or_url, num_results=limit)
    urls = [item.get("url") for item in exa.get("items", []) if item.get("url")]
    if not urls:
        return _mock(query_or_url, limit)

    gathered = await asyncio.gather(*[asyncio.to_thread(_scrape_sync, url, key) for url in urls[:limit]])
    items: list[dict[str, Any]] = []
    for block in gathered:
        items.extend(block.get("items", []))
    return {"tool": "firecrawl", "query": query_or_url, "items": items[:limit], "sources": ["firecrawl", "exa"]}


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
            {"source": "firecrawl", "title": f"Landing page pattern: {query}", "url": None, "snippet": "Mock Firecrawl result: competitors emphasize speed, integrations, ROI calculators, and social proof."},
            {"source": "firecrawl", "title": f"Messaging gaps: {query}", "url": None, "snippet": "Mock Firecrawl result: few competitors speak directly to the niche workflow or first-week activation."},
        ][:limit],
        "sources": ["firecrawl"],
        "mock": True,
    }
