"""Lightweight web search without a browser runtime."""

from __future__ import annotations

import asyncio
import html
import re
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen


async def search(query: str, limit: int = 5) -> dict:
    return await asyncio.to_thread(_search_sync, query, limit)


def _search_sync(query: str, limit: int) -> dict:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CoFound/1.0)",
            "Accept": "text/html",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read(1_000_000).decode("utf-8", errors="ignore")
        items = _parse_results(body, limit)
        return {
            "tool": "web",
            "query": query,
            "items": items,
            "sources": ["web"],
            **({"fallback": True} if not items else {}),
        }
    except Exception as exc:
        return {
            "tool": "web",
            "query": query,
            "items": [],
            "sources": ["web"],
            "error": str(exc),
        }


def _parse_results(body: str, limit: int) -> list[dict[str, str | None]]:
    blocks = re.findall(
        r'<div[^>]+class="[^"]*\bresult\b[^"]*"[^>]*>(.*?)</div>\s*</div>',
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    items: list[dict[str, str | None]] = []
    for block in blocks:
        link = re.search(
            r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not link:
            continue
        snippet_match = re.search(
            r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>',
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        title = _clean(link.group(2))
        if not title:
            continue
        items.append(
            {
                "source": "web",
                "origin": "web",
                "title": title[:240],
                "url": _result_url(html.unescape(link.group(1))),
                "snippet": _clean(snippet_match.group(1) if snippet_match else title)[:1000],
            }
        )
        if len(items) >= limit:
            break
    return items


def _result_url(value: str) -> str:
    parsed = urlparse(value)
    target = parse_qs(parsed.query).get("uddg", [value])[0]
    return unquote(target)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
