import logging
from typing import Any
import categorize_ticket
import prioritize_ticket
import kb_lookup

logger = logging.getLogger(__name__)


async def build_ticket_graph(ticket_state: Any) -> dict:
    try:
        from langgraph.graph import StateGraph
        from app.models import TicketState

        builder = StateGraph(TicketState)

        try:
            if hasattr(builder, "add_node"):
                builder.add_node(ticket_state.dict())
            elif hasattr(builder, "add_state"):
                builder.add_state(ticket_state)
        except Exception:
            # Non-fatal: graph may require a different integration.
            logger.debug("StateGraph exists but couldn't add initial state.")

        builder.add_node("category", categorize_ticket)
        builder.add_node("priority",prioritize_ticket)
        builder.add_node("knowledge_base_lookup", kb_lookup)

        return {"built": True, "builder": builder.__class__.__name__}

    except Exception as e:
        logger.debug(f"langgraph unavailable or failed to build graph: {e}")
        return {"built": False, "reason": str(e)}
