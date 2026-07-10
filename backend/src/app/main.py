import logging
from fastapi import FastAPI
from app.routers.process_ticket_router import ticket_router
from app.worker import start_consumer

from app.services.kb_lookup import ensure_nltk_resources

from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Ticket Router",
    version="1.0"
)

# Configure CORS origins
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ticket_router)

rabbitmq_connection = None

@app.on_event("startup")
async def startup_event():
    global rabbitmq_connection
    logger.info("Ensuring database indexes exist...")
    try:
        from app.services.database import ensure_db_indexes
        await ensure_db_indexes()
    except Exception as e:
        logger.error(f"Failed to verify/create database indexes: {e}")

    logger.info("Ensuring NLTK resources are installed...")
    try:
        ensure_nltk_resources()
        logger.info("NLTK resources successfully verified/downloaded.")
    except Exception as e:
        logger.error(f"Failed to verify NLTK resources: {e}")

    logger.info("Ensuring knowledge base embeddings exist in database...")
    try:
        from app.services.kb_lookup import seed_kb_embeddings_if_empty
        await seed_kb_embeddings_if_empty()
    except Exception as e:
        logger.error(f"Failed to seed/verify knowledge base embeddings: {e}")

    logger.info("Starting RabbitMQ background consumer worker...")
    try:
        rabbitmq_connection = await start_consumer()
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")
        rabbitmq_connection = None

@app.on_event("shutdown")
async def shutdown_event():
    global rabbitmq_connection
    if rabbitmq_connection:
        logger.info("Closing RabbitMQ consumer connection...")
        await rabbitmq_connection.close()