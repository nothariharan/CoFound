import os
from motor.motor_asyncio import AsyncIOMotorClient
from backend.db.collections import Collection

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    min_pool_size = int(os.getenv("MONGODB_MIN_POOL_SIZE", 5))
    max_pool_size = int(os.getenv("MONGODB_MAX_POOL_SIZE", 100))
    db.client = AsyncIOMotorClient(
        os.getenv("MONGODB_URI"),
        minPoolSize=min_pool_size,
        maxPoolSize=max_pool_size
    )
    db.database = db.client[os.getenv("MONGODB_NAME", "cofound_db")]
    print("Connected to MongoDB!")

    # Create indexes for optimization
    await db.database[Collection.DECISION_JOURNAL].create_index(
        [("node_id", 1), ("timestamp", 1)],
        name="node_id_timestamp_idx"
    )
    await db.database[Collection.WORKSPACES].create_index(
        [("_id", 1), ("nodes.node_id", 1)],
        name="workspace_id_node_id_idx"
    )
    print("MongoDB indexes ensured.")


async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection.")
