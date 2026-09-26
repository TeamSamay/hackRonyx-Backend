import asyncio
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging import logger

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

mongo_db = MongoDB()

async def connect_to_mongo():
    try:
        logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URL} (Database: {settings.MONGODB_DB_NAME})")
        mongo_db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=3000
        )
        mongo_db.db = mongo_db.client[settings.MONGODB_DB_NAME]
        
        # Ping MongoDB to verify connection
        await mongo_db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")

        # Create Indexes
        await mongo_db.db.cases.create_index("case_id", unique=True)
        await mongo_db.db.evidence.create_index("evidence_id", unique=True)
        await mongo_db.db.evidence.create_index("case_id")
        await mongo_db.db.documents.create_index("document_id", unique=True)
        await mongo_db.db.decisions.create_index("case_id")
        await mongo_db.db.connectors.create_index("connector_id", unique=True)
        logger.info("MongoDB collections and indexes initialized successfully.")
    except Exception as e:
        logger.warning(f"MongoDB connection notice: {e}. If local MongoDB is not running, ensure MongoDB service is active or configure MONGODB_URL in .env.")

async def close_mongo_connection():
    if mongo_db.client:
        logger.info("Closing MongoDB connection...")
        mongo_db.client.close()
        logger.info("MongoDB connection closed.")

def get_database() -> Optional[AsyncIOMotorDatabase]:
    return mongo_db.db
