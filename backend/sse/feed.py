"""server sent events live stream helpers"""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict, defaultdict, deque
from typing import Any, AsyncIterator


class SSEFeed:
    def __init__(self, history_size: int = 50, max_workspaces: int = 200) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._history: OrderedDict[str, deque[dict[str, Any]]] = OrderedDict()
        self._history_size = history_size
        self._max_workspaces = max_workspaces

    async def publish(self, workspace_id: str, event: dict[str, Any]) -> None:
        payload = {
            "text": event.get("text", ""),
            "type": event.get("type", "info"),
            **({"node_id": event["node_id"]} if event.get("node_id") else {}),
            **({"score": event["score"]} if event.get("score") is not None else {}),
            **({"workspace": event["workspace"]} if event.get("workspace") else {}),
            **({"dialogue": event["dialogue"]} if event.get("dialogue") else {}),
        }
        history = self._history.setdefault(workspace_id, deque(maxlen=self._history_size))
        history.append(payload)
        self._history.move_to_end(workspace_id)
        self._prune_history()
        for queue in list(self._subscribers.get(workspace_id, set())):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                # drop slow consumers; browser will reconnect and replay recent history
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

    def _prune_history(self) -> None:
        while len(self._history) > self._max_workspaces:
            removable = next(
                (workspace_id for workspace_id in self._history if not self._subscribers.get(workspace_id)),
                None,
            )
            if removable is None:
                return
            self._history.pop(removable, None)


feed = SSEFeed()
