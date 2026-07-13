import logging
import os
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from app.models import TicketState
from app.services.categorize_ticket import categorize_ticket
from app.services.prioritize_ticket import prioritize_ticket
from app.services.kb_lookup import kb_lookup
from utils.config import CLASSIFICATION_MODEL, REPLY_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class TicketValidationResult(BaseModel):
    is_in_domain: bool = Field(description="True if the message is in the customer support ticketing domain for TechEase Cloud. False if it is coding help, jokes, humor, memes, politics, medical questions, or general chat.")
    is_answerable: bool = Field(description="True if the provided Knowledge Base Context contains the exact information required to answer the customer message. False if the context is missing, irrelevant, or does not directly address the customer message.")

async def node_categorize(state: TicketState) -> dict:
    return await categorize_ticket(state)

async def node_prioritize(state: TicketState) -> dict:
    return await prioritize_ticket(state)

async def node_kb_lookup(state: TicketState) -> dict:
    return await kb_lookup(state)

async def node_context_buildup(state: TicketState) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found for validation. Skipping validation.")
        return {}
        
    try:
        llm = ChatGoogleGenerativeAI(model=CLASSIFICATION_MODEL, google_api_key=api_key)
        structured_llm = llm.with_structured_output(TicketValidationResult)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert customer support ticket validator for TechEase Cloud.\n"
                "Your job is to analyze the Customer Message and the provided Knowledge Base Context to determine:\n"
                "1. If the message is within the customer support ticketing domain (e.g. billing, invoices, account actions/settings like password resets, email changes, bug reporting, technical features). Note that general account actions/settings and billing inquiries are fully IN-DOMAIN. If the message is about memes/humor, politics, general coding/programming help (unrelated to using the TechEase API platform), medical/health advice, or general chat unrelated to customer support, set 'is_in_domain' to False.\n"
                "2. If the provided Knowledge Base Context contains the exact details/information required to address the customer's specific question. If the context is empty, generic, or does not contain the specific answer (for example, if the customer asks how to permanently delete their account but the KB context does not mention how to permanently delete their account), set 'is_answerable' to False."
            )),
            ("human", (
                "Customer Message: {message}\n\n"
                "Provided Knowledge Base Context:\n{kb_context}\n\n"
                "Perform validation:"
            ))
        ])
        
        chain = prompt | structured_llm
        result = await chain.ainvoke({
            "message": state.message,
            "kb_context": state.kb_context
        })
        
        logger.info(f"Ticket validation result: is_in_domain={result.is_in_domain}, is_answerable={result.is_answerable}")
        
        return {
            "escalation_required": result.is_in_domain and not result.is_answerable,
            "is_in_domain": result.is_in_domain
        }
            
    except Exception as e:
        logger.error(f"Error in ticket validation: {e}")
        
    return {}

async def node_auto_reply(state: TicketState) -> dict:
    if not state.is_in_domain:
        reply = (
            "I am an AI agent designed to assist you with the following.\n\n"
            "TechEase Cloud provides:\n"
            "● Cloud storage\n"
            "● Team collaboration\n"
            "● Subscription plans\n"
            "● API platform\n\n"
            "and their account related stuff."
        )
        return {
            "reply_message": reply,
            "auto_reply_sent": True,
            "routed_to_queue": False,
            "escalation_required": False
        }

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found for auto-reply. Using default template.")
        reply = f"Hello {state.customer_name or 'Customer'},\n\nThank you for reaching out. Based on your message, we found the following information from our knowledge base:\n\n{state.kb_context}\n\nHope this helps! Let us know if you need anything else."
    else:
        try:
            llm = ChatGoogleGenerativeAI(model=REPLY_MODEL, google_api_key=api_key)
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a helpful, professional customer support agent. "
                    "Draft a helpful response to the customer using ONLY the provided Knowledge Base context. "
                    "Do NOT make up any information or suggest steps that are not explicitly present in the Knowledge Base context. "
                    "If the Knowledge Base context does not contain the exact instructions or information to address the customer's request, "
                    "or if the request is not related to customer support (e.g. coding help, humor, politics), you MUST reply with exactly '[ESC]' "
                    "and nothing else. "
                    "Address the customer by name if provided. Use a polite tone and sign off as 'Support Team'."
                )),
                ("human", (
                    "Customer Name: {customer_name}\n"
                    "Customer Message: {message}\n\n"
                    "Relevant Knowledge Base Context:\n{kb_context}\n\n"
                    "Draft the reply response:"
                ))
            ])
            
            chain = prompt | llm
            response = await chain.ainvoke({
                "customer_name": state.customer_name or "Customer",
                "message": state.message,
                "kb_context": state.kb_context
            })
            if isinstance(response.content, str):
                reply = response.content
            elif isinstance(response.content, list):
                reply_parts = []
                for part in response.content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        reply_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        reply_parts.append(part)
                reply = "".join(reply_parts)
            else:
                reply = str(response.content)

            if reply.strip() == "[ESC]" or "[ESC]" in reply:
                logger.info("Auto-reply LLM returned [ESC] or detected unanswerable query. Escalating to user queue.")
                dept = state.department or "General Support"
                escalation_reply = f"Your ticket has been routed to the {dept} department. A representative will contact you shortly."
                return {
                    "reply_message": escalation_reply,
                    "auto_reply_sent": False,
                    "routed_to_queue": True,
                    "escalation_required": True
                }
        except Exception as e:
            logger.error(f"Error generating LLM auto-reply: {e}. Falling back to default template.")
            reply = f"Hello {state.customer_name or 'Customer'},\n\nThank you for reaching out. Based on your message, we found the following information from our knowledge base:\n\n{state.kb_context}\n\nHope this helps! Let us know if you need anything else."
            
    return {
        "reply_message": reply,
        "auto_reply_sent": True,
        "routed_to_queue": False
    }

async def node_user_queue(state: TicketState) -> dict:
    dept = state.department or "General Support"
    reply = f"Your ticket has been routed to the {dept} department. A representative will contact you shortly."
    return {
        "reply_message": reply,
        "auto_reply_sent": False,
        "routed_to_queue": True
    }

def route_auto_reply(state: TicketState) -> str:
    if state.escalation_required:
        return "user_queue"
    return "auto_reply"

def build_ticket_graph():
    builder = StateGraph(TicketState)
    
    builder.add_node("category", node_categorize)
    builder.add_node("priority", node_prioritize)
    builder.add_node("kb_lookup", node_kb_lookup)
    builder.add_node("context_buildup", node_context_buildup)
    builder.add_node("auto_reply", node_auto_reply)
    builder.add_node("user_queue", node_user_queue)
    
    builder.add_edge(START, "category")
    builder.add_edge(START, "priority")
    builder.add_edge(START, "kb_lookup")
    
    builder.add_edge("category", "context_buildup")
    builder.add_edge("priority", "context_buildup")
    builder.add_edge("kb_lookup", "context_buildup")
    
    builder.add_conditional_edges(
        "context_buildup",
        route_auto_reply,
        {
            "auto_reply": "auto_reply",
            "user_queue": "user_queue"
        }
    )
    
    builder.add_edge("auto_reply", END)
    builder.add_edge("user_queue", END)
    
    return builder.compile()
