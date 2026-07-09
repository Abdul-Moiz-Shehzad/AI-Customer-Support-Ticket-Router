import logging
from app.models import TicketInput, TicketState
from app.services.graph_builder import build_ticket_graph
from app.services.database import save_ticket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ticket_graph = build_ticket_graph()

async def process_ticket_service(ticket: TicketInput):
    initial_state = TicketState(
        ticket_id=ticket.ticket_id,
        customer_name=ticket.customer_name,
        customer_email=ticket.customer_email,
        subscription=ticket.subscription,
        message=ticket.message
    )

    try:
        final_state = await ticket_graph.ainvoke(initial_state)
        
        if isinstance(final_state, dict):
            category = final_state.get("category", "")
            priority = final_state.get("priority", "")
            department = final_state.get("department", "Support")
            escalation_required = final_state.get("escalation_required", False)
            reply_message = final_state.get("reply_message", "")
            auto_reply_sent = final_state.get("auto_reply_sent", False)
        else:
            category = getattr(final_state, "category", "")
            priority = getattr(final_state, "priority", "")
            department = getattr(final_state, "department", "Support")
            escalation_required = getattr(final_state, "escalation_required", False)
            reply_message = getattr(final_state, "reply_message", "")
            auto_reply_sent = getattr(final_state, "auto_reply_sent", False)

        result = {
            "ticket_id": ticket.ticket_id,
            "customer_name": ticket.customer_name,
            "customer_email": ticket.customer_email,
            "subscription": ticket.subscription,
            "message": ticket.message,
            "category": category,
            "priority": priority,
            "department": department,
            "escalation_required": escalation_required,
            "reply_message": reply_message,
            "auto_reply_sent": auto_reply_sent,
            "graph": {"built": True}
        }
        await save_ticket(result)
        return result

    except Exception as e:
        logger.error(f"Error running LangGraph: {e}")
        from app.services.categorize_ticket import fallback_categorize
        from app.services.prioritize_ticket import fallback_prioritize
        
        cat_dept = fallback_categorize(ticket.message)
        pri_esc = fallback_prioritize(ticket.message, ticket.subscription)
        
        dept = cat_dept["department"]
        escalation_required = pri_esc["escalation_required"]
        
        if escalation_required:
            reply = f"Your ticket has been routed to the {dept} department. A representative will contact you shortly."
            sent = False
        else:
            from app.services.kb_lookup import search_kb
            kb_context = search_kb(ticket.message, cat_dept["category"])
            reply = f"Hello {ticket.customer_name},\n\nThank you for reaching out. Based on your message, we found the following information from our knowledge base:\n\n{kb_context}\n\nHope this helps!"
            sent = True

        result = {
            "ticket_id": ticket.ticket_id,
            "customer_name": ticket.customer_name,
            "customer_email": ticket.customer_email,
            "subscription": ticket.subscription,
            "message": ticket.message,
            "category": cat_dept["category"],
            "priority": pri_esc["priority"],
            "department": dept,
            "escalation_required": escalation_required,
            "reply_message": reply,
            "auto_reply_sent": sent,
            "graph": {"built": False, "reason": str(e)}
        }
        await save_ticket(result)
        return result