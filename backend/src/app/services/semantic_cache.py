from datetime import datetime
import logging
from app.services.database import cache_collection
from app.services.embeddings import generate_embedding_single, cosine_similarity

logger = logging.getLogger(__name__)

async def get_cached_ticket(message: str, threshold: float = 0.70) -> dict | None:
    if cache_collection is None:
        logger.warning("MongoDB cache collection is not initialized. Skipping cache lookup.")
        return None

    try:
        # Generate query embedding
        query_embedding = await generate_embedding_single(message)
        
        # Query all cached tickets
        cursor = cache_collection.find({})
        best_match = None
        best_similarity = -1.0
        
        async for doc in cursor:
            cached_embedding = doc.get("embedding")
            if not cached_embedding:
                continue
                
            sim = cosine_similarity(query_embedding, cached_embedding)
            if sim > best_similarity:
                best_similarity = sim
                best_match = doc

        if best_match and best_similarity >= threshold:
            logger.info(f"Semantic cache hit! Similarity: {best_similarity:.4f} (threshold: {threshold})")
            
            # Update last_accessed_at for LRU behavior
            try:
                await cache_collection.update_one(
                    {"_id": best_match["_id"]},
                    {"$set": {"last_accessed_at": datetime.utcnow()}}
                )
            except Exception as e:
                logger.error(f"Failed to update last_accessed_at for cache entry: {e}")
                
            return best_match
            
        logger.info(f"Semantic cache miss. Best match similarity: {best_similarity:.4f} (threshold: {threshold})")
        return None
    except Exception as e:
        logger.error(f"Error checking semantic cache: {e}")
        return None

async def add_to_cache(message: str, result: dict) -> None:
    if cache_collection is None:
        logger.warning("MongoDB cache collection is not initialized. Cannot add to cache.")
        return

    try:
        # Generate embedding for the cached message
        embedding = await generate_embedding_single(message)
        
        cache_entry = {
            "message": message,
            "embedding": embedding,
            "category": result.get("category", ""),
            "priority": result.get("priority", ""),
            "department": result.get("department", ""),
            "escalation_required": result.get("escalation_required", False),
            "reply_message": result.get("reply_message", ""),
            "auto_reply_sent": result.get("auto_reply_sent", False),
            "last_accessed_at": datetime.utcnow()
        }
        
        # Upsert based on the exact message content
        await cache_collection.update_one(
            {"message": message},
            {"$set": cache_entry},
            upsert=True
        )
        logger.info("Successfully saved ticket details to semantic cache.")
    except Exception as e:
        logger.error(f"Failed to save ticket to semantic cache: {e}")
