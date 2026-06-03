"""Node read/write/update operations — wired to MongoDB in Day 1-2."""

from graph.schema import BaseNode, WorkspaceDocument


class NodeManager:
    """Manages node CRUD against MongoDB Atlas."""

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        raise NotImplementedError("MongoDB connection pending Day 1-2")

    async def save_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        raise NotImplementedError("MongoDB connection pending Day 1-2")

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        raise NotImplementedError("MongoDB connection pending Day 1-2")
