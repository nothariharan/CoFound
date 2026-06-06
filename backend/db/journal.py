from datetime import datetime
from backend.db.connection import db
from backend.db.collections import Collection

async def append_to_decision_journal(node_id: str, update_data: dict):
    journal_entry = {
        "timestamp": datetime.utcnow(),
        "node_id": node_id,
        "update_data": update_data
    }
    await db.database[Collection.DECISION_JOURNAL].insert_one(journal_entry)
    print(f"Appended to decision journal for node {node_id}")

async def append_to_historical_snapshots(node_id: str, current_node_data: dict):
    snapshot_entry = {
        "timestamp": datetime.utcnow(),
        "node_id": node_id,
        "snapshot": current_node_data
    }
    await db.database[Collection.HISTORICAL_SNAPSHOTS].insert_one(snapshot_entry)
    print(f"Appended to historical snapshots for node {node_id}")
