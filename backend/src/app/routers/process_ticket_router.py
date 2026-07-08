import fastapi
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.process_ticket_service import process_ticket_service
from app.models import TicketInput
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ticket_router = APIRouter()


@ticket_router.post("/classify")
async def process_ticket(ticket: TicketInput) -> dict[str,any]:
    """
Process a ticket and return a dictionary of results.
Processing involves:

1. Categorizing the ticket
2. Deciding Priority
3. Knowledge Base Lookup
4. Automatic Reply
"""
    logger.info(f"started processing ticket: {ticket.ticket_id}")
    try:
        result = await process_ticket_service(ticket)
        return result

    except Exception as e:
        logger.error(f"Error processing ticket {ticket.ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )