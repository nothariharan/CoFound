from datetime import datetime
from typing import Any

from backend.db.connection import db
from backend.db.collections import Collection
from backend.graph.schema import BaseNode, WorkspaceDocument, create_core_idea_node


class NodeManager:
    """Manages node CRUD against MongoDB Atlas."""

    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None:
        """Retrieves a workspace document from MongoDB."""
        doc = await db.db[Collection.WORKSPACES].find_one({"_id": idea_id})
        if doc:
            # Update last_active timestamp
            await db.db[Collection.WORKSPACES].update_one(
                {"_id": idea_id},
                {"$set": {"last_active": datetime.utcnow()}}
            )
            return WorkspaceDocument(**doc)
        return None

    async def save_workspace(self, workspace: WorkspaceDocument) -> WorkspaceDocument:
        """Saves or updates a workspace document in MongoDB."""
        workspace.last_active = datetime.utcnow()
        # Convert Pydantic model to dictionary, excluding unset fields and by alias
        workspace_dict = workspace.model_dump(by_alias=True, exclude_unset=True)

        # MongoDB uses _id, so we map idea_id to _id for primary key behavior
        workspace_dict["_id"] = workspace_dict["idea_id"]
        del workspace_dict["idea_id"]

        result = await db.db[Collection.WORKSPACES].update_one(
            {"_id": workspace_dict["_id"]},
            {"$set": workspace_dict},
            upsert=True
        )
        # If it was an insert, ensure the idea_id is set back correctly
        if result.upserted_id:
            workspace.idea_id = str(result.upserted_id)
        return workspace

    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode:
        """Updates a specific node within a workspace document in MongoDB."""
        node.last_updated = datetime.utcnow()
        # Convert Pydantic model to dictionary, excluding unset fields and by alias
        node_dict = node.model_dump(by_alias=True, exclude_unset=True)

        result = await db.db[Collection.WORKSPACES].update_one(
            {"_id": idea_id, "nodes.node_id": node.node_id},
            {"$set": {
                "nodes.$[elem]": node_dict,
                "last_active": datetime.utcnow()
            }},
            array_filters=[{"elem.node_id": node.node_id}]
        )

        if result.modified_count == 0:
            # If node was not found for update, try to add it to the array
            add_result = await db.db[Collection.WORKSPACES].update_one(
                {"_id": idea_id},
                {"$push": {"nodes": node_dict}, "$set": {"last_active": datetime.utcnow()}}
            )
            if add_result.modified_count == 0:
                pass

        return node

    async def create_workspace_with_core_idea(self, idea: str) -> WorkspaceDocument:
        """Creates a new workspace with an initial Core Idea node."""
        core_idea_node = create_core_idea_node(idea)
        workspace = WorkspaceDocument(
            workspace_name=f"Startup Idea: {idea[:50]}...",
            nodes=[core_idea_node]
        )
        return await self.save_workspace(workspace)

    async def delete_workspace(self, idea_id: str) -> bool:
        """Deletes an entire workspace document from MongoDB."""
        result = await db.db[Collection.WORKSPACES].delete_one({"_id": idea_id})
        return result.deleted_count > 0

    async def delete_node(self, idea_id: str, node_id: str) -> bool:
        """Deletes a specific node from a workspace's nodes array in MongoDB."""
        result = await db.db[Collection.WORKSPACES].update_one(
            {"_id": idea_id},
            {"$pull": {"nodes": {"node_id": node_id}}, "$set": {"last_active": datetime.utcnow()}}
        )
        return result.modified_count > 0
