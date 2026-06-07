import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_DETAILS = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGODB_DB")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_db():
    db.client = AsyncIOMotorClient(MONGO_DETAILS)
    db.db = db.client[MONGO_DB_NAME]
    print(f"Connected to MongoDB: {MONGO_DB_NAME}")

async def close_db():
    db.client.close()
    print("Closed MongoDB connection")
