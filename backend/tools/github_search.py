"""GitHub Search API — open source landscape + build events."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


async def search_repositories(query: str, limit: int = 5) -> dict[str, Any]:
    return await asyncio.to_thread(_search_sync, query, limit)


async def recent_commits(repo: str, limit: int = 10, token: str | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(_commits_sync, repo, limit, token)


def _headers(token: str | None = None) -> dict[str, str]:
    token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CoFoundBuildObserver/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _search_sync(query: str, limit: int) -> dict[str, Any]:
    url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&per_page={limit}"
    try:
        with urlopen(Request(url, headers=_headers()), timeout=25) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        items = [{"source": "github", "title": r.get("full_name"), "url": r.get("html_url"), "snippet": r.get("description") or "", "stars": r.get("stargazers_count", 0)} for r in data.get("items", [])]
        return {"tool": "github", "query": query, "items": items, "sources": ["github"]}
    except Exception as exc:
        return {"tool": "github", "query": query, "items": [], "sources": ["github"], "error": str(exc)}


def _commits_sync(repo: str, limit: int, token: str | None) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/commits?per_page={limit}"
    try:
        with urlopen(Request(url, headers=_headers(token)), timeout=25) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        items = [{"source": "github", "sha": c.get("sha"), "message": c.get("commit", {}).get("message"), "author": c.get("commit", {}).get("author", {}).get("name"), "date": c.get("commit", {}).get("author", {}).get("date"), "url": c.get("html_url")} for c in data]
        return {"tool": "github_commits", "repo": repo, "items": items, "sources": ["github"]}
    except Exception as exc:
        return {"tool": "github_commits", "repo": repo, "items": [], "sources": ["github"], "error": str(exc)}
