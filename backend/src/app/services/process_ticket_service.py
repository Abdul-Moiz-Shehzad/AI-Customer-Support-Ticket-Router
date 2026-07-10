import logging
from app.models import TicketInput, TicketState
from app.services.graph_builder import build_ticket_graph
from app.services.database import save_ticket
from app.services.semantic_cache import get_cached_ticket, add_to_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ticket_graph = build_ticket_graph()

async def process_ticket_service(ticket: TicketInput):
    # Try semantic cache lookup first
    try:
        cached_result = await get_cached_ticket(ticket.message)
        if cached_result:
            logger.info(f"Semantic Cache HIT for ticket: {ticket.ticket_id}")
            result = {
                "ticket_id": ticket.ticket_id,
                "customer_name": ticket.customer_name,
                "customer_email": ticket.customer_email,
                "subscription": ticket.subscription,
                "message": ticket.message,
                "category": cached_result.get("category", ""),
                "priority": cached_result.get("priority", ""),
                "department": cached_result.get("department", "Support"),
                "escalation_required": cached_result.get("escalation_required", False),
                "reply_message": cached_result.get("reply_message", ""),
                "auto_reply_sent": cached_result.get("auto_reply_sent", False),
                "cache_hit": True,
                "graph": {"built": True, "cached": True}
            }
            await save_ticket(result)
            return result
    except Exception as cache_err:
        logger.error(f"Error checking semantic cache: {cache_err}. Proceeding to LangGraph.")

    # Cache miss - build initial state for LangGraph
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
            "cache_hit": False,
            "graph": {"built": True}
        }
        await save_ticket(result)
        
        # Save to semantic cache
        await add_to_cache(ticket.message, result)
        
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
            kb_context = await search_kb(ticket.message, cat_dept["category"])
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
            "cache_hit": False,
            "graph": {"built": False, "reason": str(e)}
        }
        await save_ticket(result)
        
        # Save fallback to semantic cache as well
        await add_to_cache(ticket.message, result)
        
        return result