from fastapi import FastAPI
from app.routers.process_ticket_router import ticket_router
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Ticket Router",
    version="1.0"
)

app.include_router(ticket_router)

