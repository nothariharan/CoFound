"""GitHub polling agent — updates Build Node every 5 minutes."""

from __future__ import annotations

from typing import Any

from agents.store_protocol import GraphStore, ResearchTask
from mdb_mcp.agent_store import get_agent_store
from llm.gemini import generate_flash
from sse.feed import feed
from tools.github_search import recent_commits


async def observe_build(workspace_id: str, repo: str, store: GraphStore | None = None, token: str | None = None) -> dict[str, Any]:
    store = store or get_agent_store()
    commits = await recent_commits(repo, limit=10, token=token)
    prompt = f"Infer shipped product features from these commits. Return concise bullets.\n{commits}"
    summary = await generate_flash(prompt, system="You are a build observer. Infer features from GitHub commits.")
    result = {"repo": repo, "summary": summary, "commits": commits.get("items", []), "sources": ["github"]}
    if hasattr(store, "commit_research_result"):
        task = ResearchTask(workspace_id=workspace_id, task=f"Observe GitHub repo {repo}", type="build", tools=["github"], priority=1)
        await getattr(store, "commit_research_result")(workspace_id, task, result, 80 if commits.get("items") else 55)
    await feed.publish(
        workspace_id,
        {
            "text": f"[Build Observer] GitHub repo {repo} observed. Commits found: {len(commits.get('items', []))}.",
            "type": "done" if commits.get("items") else "info",
        },
    )
    return result
