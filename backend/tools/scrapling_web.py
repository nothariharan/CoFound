"""Broad web/community research using Scrapling.

Scrapling is used for wide, low-cost web discovery. Firecrawl remains the
targeted scraper for specific pages and high-intent searches.
"""

from __future__ import annotations

import asyncio
import html
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus, urljoin


@dataclass(frozen=True)
class SearchTarget:
    url: str
    origin: str
    selector: str


async def search_broad(query: str, limit: int = 5) -> dict[str, Any]:
    """Search broad community/web surfaces and return CoFounder tool JSON."""

    return await asyncio.to_thread(_search_broad_sync, query, limit)


def _search_broad_sync(query: str, limit: int) -> dict[str, Any]:
    targets = [
        SearchTarget(
            url=f"https://old.reddit.com/search?q={quote_plus(query)}&sort=relevance",
            origin="reddit",
            selector="div.search-result, div.thing",
        ),
        SearchTarget(
            url=f"https://duckduckgo.com/html/?q={quote_plus(f'site:reddit.com {query}')}",
            origin="web",
            selector=".result",
        ),
        SearchTarget(
            url=f"https://duckduckgo.com/html/?q={quote_plus(query)}",
            origin="web",
            selector=".result",
        ),
    ]

    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for target in targets:
        if len(items) >= limit:
            break
        try:
            page = _fetch_tiered(target.url)
            items.extend(_extract_items(page, target, query, limit - len(items)))
        except Exception as exc:  # pragma: no cover - exercised via mocked fetch tests
            errors.append(f"{target.origin}: {exc}")

    items = _dedupe_items(items)[:limit]
    if items:
        return {"tool": "scrapling", "query": query, "items": items, "sources": ["scrapling", "web"]}

    return {
        "tool": "scrapling",
        "query": query,
        "items": [
            {
                "source": "web",
                "origin": "web",
                "title": f"Web scrape unavailable for: {query}",
                "url": None,
                "snippet": "Web scrape failed after HTTP + stealth attempts; check scrapling install or query.",
            }
        ],
        "sources": ["scrapling", "web"],
        "fallback": True,
        "error": "; ".join(errors) if errors else "No web results found.",
    }


def _fetch_tiered(url: str) -> Any:
    """Try Scrapling's lightweight HTTP fetch first, then browser stealth."""

    try:
        from scrapling.fetchers import FetcherSession

        with FetcherSession(impersonate="chrome") as session:
            page = session.get(url, stealthy_headers=True, timeout=30)
        if _page_has_text(page):
            return page
    except Exception:
        pass

    from scrapling.fetchers import StealthyFetcher

    page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=45000)
    if not _page_has_text(page):
        raise RuntimeError("Scrapling returned an empty page")
    return page


def _page_has_text(page: Any) -> bool:
    text = _safe_text(page)
    return len(text.strip()) > 100


def _extract_items(page: Any, target: SearchTarget, query: str, limit: int) -> list[dict[str, Any]]:
    if target.origin == "reddit":
        return _extract_reddit_items(page, target.url, query, limit)
    return _extract_duckduckgo_items(page, target.url, query, limit)


def _extract_reddit_items(page: Any, base_url: str, query: str, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for block in _select(page, "div.search-result, div.thing")[:limit]:
        title = _first_text(block, "a.search-title, a.title")
        href = _first_attr(block, "a.search-title, a.title", "href")
        snippet = _first_text(block, ".search-result-body, .search-expando, .usertext-body, .md")
        if not title:
            continue
        items.append(_item("reddit", title, _absolute_url(base_url, href), snippet or title))

    if items:
        return items
    return _fallback_text_items(_safe_text(page), query, "reddit", limit)


def _extract_duckduckgo_items(page: Any, base_url: str, query: str, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for block in _select(page, ".result, .web-result")[:limit]:
        title = _first_text(block, ".result__title a, a.result__a")
        href = _first_attr(block, ".result__title a, a.result__a", "href")
        snippet = _first_text(block, ".result__snippet, .result__body")
        if not title:
            continue
        origin = "reddit" if "reddit.com" in (href or "") else "web"
        items.append(_item(origin, title, _absolute_url(base_url, href), snippet or title))

    if items:
        return items
    return _fallback_text_items(_safe_text(page), query, "web", limit)


def _fallback_text_items(text: str, query: str, origin: str, limit: int) -> list[dict[str, Any]]:
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 60]
    return [
        _item(origin, f"{origin.title()} evidence for {query}", None, line[:600])
        for line in lines[:limit]
    ]


def _item(origin: str, title: str, url: str | None, snippet: str) -> dict[str, Any]:
    return {
        "source": "web",
        "origin": origin,
        "title": _clean_text(title)[:240],
        "url": url,
        "snippet": _clean_text(snippet)[:1000],
    }


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = item.get("url") or item.get("title") or item.get("snippet")
        if not key or key in seen:
            continue
        seen.add(str(key))
        deduped.append(item)
    return deduped


def _select(page: Any, selector: str) -> list[Any]:
    try:
        return list(page.css(selector))
    except Exception:
        return []


def _first_text(block: Any, selector: str) -> str:
    try:
        selected = block.css(f"{selector}::text")
        value = selected.get()
        if value:
            return _clean_text(str(value))
    except Exception:
        pass
    try:
        selected = block.css(selector)
        first = selected[0] if selected else None
        if first is not None:
            return _clean_text(_safe_text(first))
    except Exception:
        pass
    return ""


def _first_attr(block: Any, selector: str, attr: str) -> str | None:
    try:
        value = block.css(f"{selector}::attr({attr})").get()
        if value:
            return _extract_attr(str(value), attr)
    except Exception:
        pass
    try:
        selected = block.css(selector)
        first = selected[0] if selected else None
        if first is not None:
            return _extract_attr(_safe_text(first), attr)
    except Exception:
        pass
    return None


def _safe_text(value: Any) -> str:
    for attr in ("text", "body"):
        candidate = getattr(value, attr, None)
        if callable(candidate):
            try:
                return str(candidate())
            except Exception:
                pass
        if candidate:
            return str(candidate)
    try:
        return str(value)
    except Exception:
        return ""


def _absolute_url(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base_url, href)


def _extract_attr(value: str, attr: str) -> str | None:
    value = value.strip()
    if "<" not in value:
        return html.unescape(value)
    match = re.search(rf'{re.escape(attr)}=["\']([^"\']+)["\']', value, flags=re.I)
    return html.unescape(match.group(1)) if match else None


def _clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()
