"""Server-Sent Events live stream helpers."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict, deque
from typing import Any, AsyncIterator


class SSEFeed:
    def __init__(self, history_size: int = 100) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=history_size))

    async def publish(self, workspace_id: str, event: dict[str, Any]) -> None:
        payload = {
            "text": event.get("text", ""),
            "type": event.get("type", "info"),
            **({"node_id": event["node_id"]} if event.get("node_id") else {}),
            **({"score": event["score"]} if event.get("score") is not None else {}),
            **({"workspace": event["workspace"]} if event.get("workspace") else {}),
            **({"dialogue": event["dialogue"]} if event.get("dialogue") else {}),
        }
        self._history[workspace_id].append(payload)
        for queue in list(self._subscribers.get(workspace_id, set())):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                # Drop slow consumers; browser will reconnect and replay recent history.
                self._subscribers[workspace_id].discard(queue)

    async def subscribe(self, workspace_id: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers[workspace_id].add(queue)
        try:
            for item in list(self._history.get(workspace_id, [])):
                yield item
            while True:
                yield await queue.get()
        finally:
            self._subscribers[workspace_id].discard(queue)

    async def stream(self, workspace_id: str, heartbeat_seconds: int = 15) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers[workspace_id].add(queue)
        try:
            for item in list(self._history.get(workspace_id, [])):
                yield item
            while True:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
                except asyncio.TimeoutError:
                    yield {"text": "", "type": "ping"}
        finally:
            self._subscribers[workspace_id].discard(queue)

    def encode(self, event: dict[str, Any]) -> dict[str, str]:
        return {"event": "message", "data": json.dumps(event)}


feed = SSEFeed()
