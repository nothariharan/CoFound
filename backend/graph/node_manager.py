from typing import List, Optional
from uuid import UUID

from backend.db.connection import db
from backend.db.collections import NODES, STARTUP_GRAPHS
from backend.graph.schema import BaseNode, WorkspaceDocument

class NodeManager:
    def __init__(self):
        self.nodes_collection = db.db[NODES]
        self.workspaces_collection = db.db[STARTUP_GRAPHS]

    async def create_node(self, node: BaseNode) -> BaseNode:
        node_dict = node.model_dump(by_alias=True)
        # Convert UUID to string for MongoDB storage
        node_dict["node_id"] = str(node.node_id)
        await self.nodes_collection.insert_one(node_dict)
        return node

    async def get_node(self, node_id: UUID) -> Optional[BaseNode]:
        node_dict = await self.nodes_collection.find_one({"node_id": str(node_id)})
        if node_dict:
            return BaseNode(**node_dict)
        return None

    async def update_node(self, node_id: UUID, updates: dict) -> Optional[BaseNode]:
        # Ensure node_id is not updated and convert UUID to string for MongoDB
        if "node_id" in updates:
            del updates["node_id"]

        result = await self.nodes_collection.update_one(
            {"node_id": str(node_id)}, {"$set": updates}
        )
        if result.modified_count:
            return await self.get_node(node_id)
        return None

    async def delete_node(self, node_id: UUID) -> bool:
        result = await self.nodes_collection.delete_one({"node_id": str(node_id)})
        return result.deleted_count > 0

    async def get_workspace_nodes(self, idea_id: UUID) -> List[BaseNode]:
        workspace_doc = await self.workspaces_collection.find_one({"idea_id": str(idea_id)})
        if workspace_doc and "nodes" in workspace_doc:
            node_ids = [node_ref["node_id"] for node_ref in workspace_doc["nodes"]]
            # Fetch full node details from the NODES collection
            nodes_data = await self.nodes_collection.find({"node_id": {"$in": node_ids}}).to_list(length=None)
            # Preserve order based on workspace_doc["nodes"]
            node_map = {UUID(node_data["node_id"]): BaseNode(**node_data) for node_data in nodes_data}
            return [node_map[UUID(node_ref["node_id"])] for node_ref in workspace_doc["nodes"] if UUID(node_ref["node_id"]) in node_map]
        return []

    async def create_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        workspace_dict = workspace.model_dump(by_alias=True)
        # Insert individual nodes first
        for node in workspace.nodes:
            await self.create_node(node)

        # Store only node_ids in the workspace document for referencing
        workspace_dict["nodes"] = [{"node_id": str(node.node_id)} for node in workspace.nodes]
        workspace_dict["idea_id"] = str(workspace.idea_id) # Convert UUID to string

        await self.workspaces_collection.insert_one(workspace_dict)
        return workspace

    async def get_workspace(self, idea_id: UUID) -> Optional[WorkspaceDocument]:
        workspace_doc = await self.workspaces_collection.find_one({"idea_id": str(idea_id)})
        if workspace_doc:
            # Fetch full node details
            nodes = await self.get_workspace_nodes(idea_id)
            workspace_doc["nodes"] = nodes
            return WorkspaceDocument(**workspace_doc)
        return None

    async def add_node_to_workspace(self, idea_id: UUID, node: BaseNode) -> Optional[WorkspaceDocument]:
        await self.create_node(node)
        result = await self.workspaces_collection.update_one(
            {"idea_id": str(idea_id)},
            {"$push": {"nodes": {"node_id": str(node.node_id)}}}
        )
        if result.modified_count:
            return await self.get_workspace(idea_id)
        return None

    async def create_workspace_with_core_idea(self, idea: str) -> WorkspaceDocument:
        core_idea_node = BaseNode(
            type="core_idea",
            title="Core Idea",
            summary=idea,
            confidence=0, # Initial confidence
            status="needs_work" # Initial status
        )

        workspace_name = idea[:50] + "..." if len(idea) > 50 else idea
        workspace = WorkspaceDocument(
            workspace_name=workspace_name,
            nodes=[core_idea_node]
        )

        await self.create_workspace(workspace)
        return workspace
