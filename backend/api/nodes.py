from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from backend.db.connection import db
from backend.db.collections import DECISION_JOURNAL
from backend.graph.schema import BaseNode, SourcePill, NodeType
from backend.graph.node_manager import NodeManager

router = APIRouter(tags=["nodes"])

node_manager = NodeManager()

class NodeUpdateRequest(BaseModel):
    idea_id: Optional[UUID] = None # Required for context, but not part of node update itself
    confidence: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[Literal["validated", "needs_work", "blocking", "locked"]] = None
    agent_notes: Optional[str] = None
    source_pills: Optional[List[SourcePill]] = None
    sources: Optional[List[Literal["reddit", "exa", "github", "posthog", "user_input"]]] = None
    active_agents: Optional[List[str]] = None
    summary: Optional[str] = None # Allow updating summary as well

class JournalEntryRequest(BaseModel):
    event: str
    reason: str
    evidence: List[str] = Field(default_factory=list)

@router.patch("/nodes/{node_id}", response_model=BaseNode)
async def update_node(node_id: UUID, update_data: NodeUpdateRequest):
    """
    Updates a node's attributes and logs the change to the decision journal.
    """
    existing_node = await node_manager.get_node(node_id)
    if not existing_node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Prepare updates dictionary, excluding None values and idea_id
    updates = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if "idea_id" in updates:
        del updates["idea_id"] # idea_id is for context, not part of node update

    # Record confidence_before for journal if confidence is being updated
    confidence_before = existing_node.confidence
    confidence_after = updates.get("confidence", confidence_before)

    # Update last_updated timestamp
    updates["last_updated"] = datetime.utcnow()

    updated_node = await node_manager.update_node(node_id, updates)

    if not updated_node:
        raise HTTPException(status_code=500, detail="Failed to update node")

    # Log to decision journal if confidence changed or other significant update
    if confidence_after != confidence_before or updates: # Log if any update occurred
        journal_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": str(node_id),
            "node_type": existing_node.type.value, # Use .value for Enum
            "event": "node_updated", # Generic event for now, can be more specific
            "reason": f"Node {existing_node.type.value} updated.",
            "evidence": [], # Populate if specific evidence is passed
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
        }
        # Add more specific reason if confidence changed
        if confidence_after != confidence_before:
            journal_entry["event"] = "confidence_updated"
            journal_entry["reason"] = f"Confidence for {existing_node.type.value} changed from {confidence_before}% to {confidence_after}%."
        
        # If agent_notes are updated, include them in reason/evidence
        if "agent_notes" in updates and updates["agent_notes"]:
            journal_entry["reason"] += f" Agent notes: {updates['agent_notes'][:100]}..." if len(updates['agent_notes']) > 100 else f" Agent notes: {updates['agent_notes']}"
            journal_entry["evidence"].append(f"Agent notes updated: {updates['agent_notes']}")

        await db.db[DECISION_JOURNAL].insert_one(journal_entry)

    # For historical_snapshots, the README implies decision_journal covers it.
    # If a separate historical_snapshots collection/field is needed, it would be implemented here.
    # For now, we consider the decision journal as the historical record.

    return updated_node
