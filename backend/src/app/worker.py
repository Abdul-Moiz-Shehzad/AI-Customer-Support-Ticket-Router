import os
import json
import asyncio
import logging
import aio_pika
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import TicketInput
from app.services.process_ticket_service import process_ticket_service

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "tickets_queue"

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            body = message.body.decode("utf-8")
            data = json.loads(body)
            logger.info(f"Worker received ticket: {data.get('ticket_id')}")
            
            ticket = TicketInput(**data)
            await process_ticket_service(ticket)
            logger.info(f"Worker successfully processed ticket: {ticket.ticket_id}")
        except Exception as e:
            logger.error(f"Worker failed to process ticket message: {e}")

async def start_consumer(loop=None):
    logger.info("Initializing RabbitMQ consumer...")
    try:
        import asyncio
        connection = await asyncio.wait_for(
            aio_pika.connect(RABBITMQ_URL, loop=loop),
            timeout=2.0
        )
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        
        logger.info(f"Listening for messages on queue: '{QUEUE_NAME}'")
        await queue.consume(process_message)
        
        return connection
    except TimeoutError:
        logger.warning("RabbitMQ connection timed out. Please verify RabbitMQ is running locally on port 5672, or update RABBITMQ_URL in your .env.")
        return None
    except Exception as e:
        logger.error(f"RabbitMQ consumer initialization failed: {e}")
        return None

async def main():
    logging.basicConfig(level=logging.INFO)
    connection = await start_consumer()
    if connection:
        try:
            await asyncio.Future()
        finally:
            await connection.close()

if __name__ == "__main__":
    asyncio.run(main())
