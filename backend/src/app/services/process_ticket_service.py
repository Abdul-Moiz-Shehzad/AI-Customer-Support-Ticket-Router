import logging
from app.models import TicketInput, TicketState
from app.services.graph_builder import build_ticket_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_ticket_service(ticket: TicketInput):
    """Build a per-request StateGraph (if available), derive simple classification, and return result."""
    # Build the internal ticket state from input
    ticket_state = TicketState(
        ticket_id=ticket.ticket_id,
        customer_name=ticket.customer_name,
        customer_email=ticket.customer_email,
        subscription=ticket.subscription,
        message=ticket.message,
        category="",
        priority="",
        sentiment="",
        escalation_required=False,
    )

    graph_info = await build_ticket_graph(ticket_state)
    
    # Lightweight placeholder classification logic (can be replaced with real models)
    # Example: simple keyword-based routing
    # msg = (ticket.message or "").lower()
    # if "refund" in msg or "charge" in msg:
    #     category = "Billing"
    #     department = "Billing"
    #     priority = "High"
    # elif "error" in msg or "bug" in msg or "not working" in msg:
    #     category = "Technical"
    #     department = "Technical"
    #     priority = "High"
    # elif "feature" in msg or "request" in msg:
    #     category = "Feature Request"
    #     department = "Product"
    #     priority = "Medium"
    # else:
    #     category = "General Inquiry"
    #     department = "Support"
    #     priority = "Low"

    # # Populate ticket_state with derived values
    # ticket_state.category = category
    # ticket_state.priority = priority
    # ticket_state.sentiment = "neutral"
    # ticket_state.escalation_required = (priority == "High")

    result = {
        "ticket_id": ticket_state.ticket_id,
        "customer_name": ticket_state.customer_name,
        "customer_email": ticket_state.customer_email,
        "subscription": ticket_state.subscription,
        "message": ticket_state.message,
        "category": ticket_state.category,
        "priority": ticket_state.priority,
        "department": department,
        "escalation_required": ticket_state.escalation_required,
        "graph": graph_info,
    }

    return result