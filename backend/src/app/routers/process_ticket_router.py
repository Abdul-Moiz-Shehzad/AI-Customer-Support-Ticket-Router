import uuid
import fastapi
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import TicketInput, TicketResponse, TicketSubmissionResponse
from app.services.rabbitmq_producer import publish_ticket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ticket_router = APIRouter()


@ticket_router.post("/classify")
async def process_ticket(ticket: TicketInput):
    """
Process a ticket by submitting it to RabbitMQ queue.
"""
    if not ticket.ticket_id:
        ticket.ticket_id = str(uuid.uuid4())

    logger.info(f"Processing ticket: {ticket.ticket_id}")
    
    #1. Create a pending ticket entry in MongoDB for tracking status
    from app.services.database import create_pending_ticket, save_ticket
    db_success = await create_pending_ticket(ticket.model_dump())
    if not db_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize ticket status in database."
        )

    #2. Queue the ticket for background processing
    try:
        success = await publish_ticket(ticket.model_dump())
    except Exception as e:
        logger.error(f"Error processing ticket {ticket.ticket_id}: {e}")
        await save_ticket(ticket.model_dump(), status="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    if not success:
        await save_ticket(ticket.model_dump(), status="failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RabbitMQ service is offline or unavailable. Failed to queue ticket."
        )
        
    return {
        "ticket_id": ticket.ticket_id,
        "status": "queued",
        "message": "Ticket submitted successfully and is being processed in the background."
    }


@ticket_router.get("/ticket/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """
Query processed ticket classification results from MongoDB.
"""
    from app.services.database import tickets_collection
    if tickets_collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    ticket = await tickets_collection.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@ticket_router.get("/tickets")
async def get_all_tickets():
    """
    Query all ticket classification results from MongoDB.
    """
    from app.services.database import tickets_collection
    if tickets_collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    tickets = []
    cursor = tickets_collection.find({}).sort("created_at", -1)
    async for ticket in cursor:
        if "_id" in ticket:
            ticket["_id"] = str(ticket["_id"])
        tickets.append(ticket)
    return tickets