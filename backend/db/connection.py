import os
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db.database = db.client[os.getenv("MONGODB_NAME", "cofound_db")]
    print("Connected to MongoDB!")

async def close_mongo_connection():
    db.client.close()
    print("Closed MongoDB connection.")
