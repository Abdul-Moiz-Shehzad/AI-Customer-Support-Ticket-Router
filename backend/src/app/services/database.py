import os
import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "ticket_router_db")

try:
    client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client[MONGO_DB]
    tickets_collection = db["tickets"]
except Exception as e:
    logger.error(f"Failed to initialize MongoDB client: {e}")
    tickets_collection = None

async def ensure_db_indexes():
    if tickets_collection is not None:
        try:
            await tickets_collection.create_index("ticket_id", unique=True)
            logger.info("MongoDB index on ticket_id verified/created.")
        except Exception as e:
            logger.error(f"Failed to create MongoDB index: {e}")


async def create_pending_ticket(ticket_data: dict) -> bool:
    if tickets_collection is None:
        logger.error("MongoDB collection is not initialized. Cannot create pending ticket.")
        return False
        
    try:
        record = ticket_data.copy()
        record["status"] = "pending"
        record["created_at"] = datetime.datetime.utcnow().isoformat()
        
        record.setdefault("category", "")
        record.setdefault("priority", "")
        record.setdefault("department", "")
        record.setdefault("escalation_required", False)
        record.setdefault("reply_message", "")
        record.setdefault("auto_reply_sent", False)
        
        await tickets_collection.insert_one(record)
        logger.info(f"Successfully created pending ticket {ticket_data.get('ticket_id')} in MongoDB.")
        return True
    except Exception as e:
        logger.error(f"Error creating pending ticket in MongoDB: {e}")
        return False


async def save_ticket(ticket_data: dict, status: str = "completed") -> bool:
    if tickets_collection is None:
        logger.error("MongoDB collection is not initialized. Cannot save ticket.")
        return False
        
    try:
        record = ticket_data.copy()
        record["status"] = status
        record["updated_at"] = datetime.datetime.utcnow().isoformat()
        
        await tickets_collection.update_one(
            {"ticket_id": record["ticket_id"]},
            {"$set": record},
            upsert=True
        )
        logger.info(f"Successfully updated/saved ticket {record.get('ticket_id')} in MongoDB with status '{status}'.")
        return True
    except Exception as e:
        logger.error(f"Error saving ticket to MongoDB: {e}")
        return False
