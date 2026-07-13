import logging
import math

logger = logging.getLogger(__name__)

_st_model = None

def get_embedding_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer model loaded successfully.")
    return _st_model

import asyncio

def _generate_embeddings_batch_sync(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts).tolist()

def _generate_embedding_single_sync(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()

async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(_generate_embeddings_batch_sync, texts)

async def generate_embedding_single(text: str) -> list[float]:
    return await asyncio.to_thread(_generate_embedding_single_sync, text)

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)
