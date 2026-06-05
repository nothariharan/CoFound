from __future__ import annotations

import asyncio
import json

from agents.store_protocol import ResearchTask
from graph.schema import NodeType
from sse.feed import SSEFeed


def test_memory_store_queue_orders_by_priority_and_marks_done(memory_store, workspace):
    async def run():
        await memory_store.enqueue_task(ResearchTask(workspace_id=workspace.idea_id, task="slow", type="audience", tools=[], priority=5))
        await memory_store.enqueue_task(ResearchTask(workspace_id=workspace.idea_id, task="fast", type="competitors", tools=[], priority=1))
        task = await memory_store.pop_pending_task(workspace.idea_id)
        await memory_store.mark_task_done(task.task_id, 88)
        return task

    task = asyncio.run(run())

    assert task.task == "fast"
    assert task.status == "done"
    assert memory_store.task_results[task.task_id]["score"] == 88


def test_memory_store_commit_research_result_creates_node_and_source_pills(memory_store, workspace):
    async def run():
        task = ResearchTask(workspace_id=workspace.idea_id, task="research audience", type="audience", tools=["reddit"], priority=1)
        return await memory_store.commit_research_result(
            workspace.idea_id,
            task,
            {
                "summary": "Restaurant owners complain about stockouts.",
                "sources": ["reddit"],
                "items": [{"source": "reddit"}, {"source": "reddit"}],
            },
            87,
        )

    node = asyncio.run(run())

    assert node.type == NodeType.AUDIENCE
    assert node.confidence == 87
    assert node.status.value == "validated"
    assert node.source_pills[0].label == "Reddit"
    assert node.source_pills[0].count == 2
    assert len(workspace.nodes) == 2


def test_memory_store_commit_preserves_existing_source_pills(memory_store, workspace):
    async def run():
        first = ResearchTask(workspace_id=workspace.idea_id, task="reddit", type="audience", tools=["reddit"], priority=1)
        second = ResearchTask(workspace_id=workspace.idea_id, task="exa", type="audience", tools=["exa"], priority=1)
        await memory_store.commit_research_result(workspace.idea_id, first, {"summary": "a", "sources": ["reddit"], "items": [{"source": "reddit"}]}, 82)
        return await memory_store.commit_research_result(workspace.idea_id, second, {"summary": "b", "sources": ["exa"], "items": [{"source": "exa"}, {"source": "exa"}]}, 84)

    node = asyncio.run(run())

    counts = {pill.label: pill.count for pill in node.source_pills}
    assert counts == {"Reddit": 1, "Exa": 2}
    assert node.sources == ["exa", "reddit"]


def test_sse_feed_replays_history_and_encodes_events():
    async def run():
        local_feed = SSEFeed(history_size=5)
        await local_feed.publish("w1", {"text": "[Critique: 63/100] Too broad", "type": "critique", "score": 63})
        stream = local_feed.stream("w1", heartbeat_seconds=1)
        first = await stream.__anext__()
        encoded = local_feed.encode(first)
        await stream.aclose()
        return first, encoded

    first, encoded = asyncio.run(run())

    assert first == {"text": "[Critique: 63/100] Too broad", "type": "critique", "score": 63}
    assert encoded["event"] == "message"
    assert json.loads(encoded["data"])["score"] == 63


def test_sse_feed_heartbeat_when_idle():
    async def run():
        local_feed = SSEFeed()
        stream = local_feed.stream("idle", heartbeat_seconds=0)
        event = await stream.__anext__()
        await stream.aclose()
        return event

    event = asyncio.run(run())

    assert event == {"text": "", "type": "ping"}
