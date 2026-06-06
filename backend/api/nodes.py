"""Node read/update routes — Day 1-2."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.db.connection import db
from backend.db.collections import Collection
from backend.db.journal import append_to_decision_journal, append_to_historical_snapshots # Added this line

router = APIRouter(tags=["nodes"])

class NodeUpdate(BaseModel):
    confidence: Optional[float] = None
    # Add other fields that can be updated if necessary

@router.patch("/nodes/{node_id}")
async def update_node(node_id: str, node_update: NodeUpdate):
    # Construct the update document
    update_data = node_update.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    # Update the node in the database
    result = await db.database[Collection.NODES].update_one(
        {"_id": node_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Node with id {node_id} not found")

    # Fetch the updated node for historical snapshot
    updated_node = await db.database[Collection.NODES].find_one({"_id": node_id})
    if not updated_node:
        # This case should ideally not happen if update_one was successful
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated node")

    # A10 - On every node mutation: append to decision_journal + historical_snapshots
    await append_to_decision_journal(node_id, update_data)
    await append_to_historical_snapshots(node_id, updated_node)

    print(f"Node {node_id} updated. Confidence: {node_update.confidence}")

    return {"message": f"Node {node_id} updated successfully"}
