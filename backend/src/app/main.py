import logging
from fastapi import FastAPI
from app.routers.process_ticket_router import ticket_router
from app.worker import start_consumer

from app.services.kb_lookup import ensure_nltk_resources

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Ticket Router",
    version="1.0"
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