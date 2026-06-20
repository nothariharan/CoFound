"""node read/write/update operations — wired to graphstore"""
from __future__ import annotations

from agents.store_protocol import DEFAULT_STORE
from graph.schema import BaseNode, WorkspaceDocument, create_core_idea_node
from graph.unlock_engine import compute_unlock_states


class NodeManager:
    """manages node crud against the active graphstore"""

    def __init__(self, store=DEFAULT_STORE) -> None:
        self.store = store

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        return await self.store.get_workspace(idea_id)

    async def save_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        return await self.store.save_workspace(workspace)

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        return await self.store.update_node(idea_id, node)

    async def create_workspace(self, idea: str) -> WorkspaceDocument:
        from uuid import uuid4

        idea_id = str(uuid4())
        core_node = create_core_idea_node(idea)
        workspace = WorkspaceDocument(
            idea_id=idea_id,
            workspace_name=idea.strip()[:60] or "Untitled Startup",
            nodes=[core_node],
        )
        if hasattr(self.store, "save_workspace"):
            return await self.store.save_workspace(workspace)
        await self.store.update_node(idea_id, core_node)
        return workspace
