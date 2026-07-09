import os
import json
import logging
import aio_pika
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "tickets_queue"

async def publish_ticket(ticket_data: dict) -> bool:
    try:
        import asyncio
        connection = await asyncio.wait_for(
            aio_pika.connect(RABBITMQ_URL),
            timeout=2.0
        )
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(QUEUE_NAME, durable=True)
            
            message_body = json.dumps(ticket_data).encode("utf-8")
            
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=QUEUE_NAME
            )
            
            logger.info(f"Published ticket {ticket_data.get('ticket_id')} to RabbitMQ.")
            return True
    except TimeoutError:
        logger.warning("RabbitMQ connection timed out. Please verify RabbitMQ is running locally on port 5672, or update RABBITMQ_URL in your .env.")
        return False
    except Exception as e:
        logger.error(f"Failed to publish ticket to RabbitMQ: {e}")
        return False
