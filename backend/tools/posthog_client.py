"""PostHog API — funnel conversion signal reading."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.request import Request, urlopen


async def get_funnel(project_id: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    project_id = project_id or os.getenv("POSTHOG_PROJECT_ID", "")
    api_key = api_key or os.getenv("POSTHOG_API_KEY", "")
    if not project_id or not api_key:
        return _mock()
    return await asyncio.to_thread(_get_funnel_sync, project_id, api_key)


def _get_funnel_sync(project_id: str, api_key: str) -> dict[str, Any]:
    url = f"https://app.posthog.com/api/projects/{project_id}/insights/trend/"
    req = Request(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        return {"tool": "posthog", "project_id": project_id, "data": data, "sources": ["posthog"]}
    except Exception as exc:
        return {"tool": "posthog", "project_id": project_id, "data": {}, "error": str(exc), "sources": ["posthog"]}


def _mock() -> dict[str, Any]:
    return {
        "tool": "posthog",
        "fallback": True,
        "label": "PostHog not connected; using minimal fallback funnel",
        "sources": ["posthog"],
        "funnel": [
            {"step": "visit", "conversion": 1.0, "previous_conversion": 1.0},
            {"step": "signup", "conversion": 0.22, "previous_conversion": 0.29},
            {"step": "activate", "conversion": 0.11, "previous_conversion": 0.14},
        ],
    }
