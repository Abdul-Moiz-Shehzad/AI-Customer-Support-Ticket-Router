import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from app.models import TicketState
from utils.config import CLASSIFICATION_MODEL

load_dotenv()
logger = logging.getLogger(__name__)

class CategorizationResult(BaseModel):
    category: str = Field(description="The category of the ticket: 'Billing', 'Technical', 'Feature Request', 'Security', 'Account', or 'General Inquiry'")
    department: str = Field(description="The department to route to: 'Billing', 'Technical', 'Product', 'Support', or 'Security'")

def fallback_categorize(message: str) -> dict:
    msg = (message or "").lower()
    import re
    words = set(re.findall(r'\w+', msg))
    if any(k in words for k in ["refund", "invoice", "charge", "billing", "payment", "subscribe", "cancel", "price"]):
        return {"category": "Billing", "department": "Billing"}
    elif any(k in words for k in ["security", "unauthorized", "compromise", "compromised", "hack", "suspicious", "abuse", "access"]):
        return {"category": "Security", "department": "Security"}
    elif any(k in words for k in ["password", "login", "reset", "lock", "locked", "email", "profile", "account"]):
        return {"category": "Account", "department": "Support"}
    elif any(k in words for k in ["error", "crash", "bug", "broken", "load", "database", "api", "integration", "fail"]):
        return {"category": "Technical", "department": "Technical"}
    elif any(k in words for k in ["feature", "request", "add", "enhance", "suggest", "update", "idea", "improvement"]):
        return {"category": "Feature Request", "department": "Product"}
    else:
        return {"category": "General Inquiry", "department": "Support"}

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

async def categorize_ticket(state: TicketState) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found. Using keyword fallback for categorization.")
        return fallback_categorize(state.message)

    try:
        llm = ChatGoogleGenerativeAI(model=CLASSIFICATION_MODEL, google_api_key=api_key)
        structured_llm = llm.with_structured_output(CategorizationResult)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert customer support ticket router. Categorize the customer support ticket message."),
            ("human", (
                "Ticket Message:\n{message}\n\n"
                "Select exactly one category from:\n"
                "- Billing\n"
                "- Technical\n"
                "- Feature Request\n"
                "- Security\n"
                "- Account\n"
                "- General Inquiry\n\n"
                "Also select the corresponding department:\n"
                "- Billing -> Billing\n"
                "- Technical -> Technical\n"
                "- Feature Request -> Product\n"
                "- Security -> Security\n"
                "- Account -> Support\n"
                "- General Inquiry -> Support"
            ))
        ])

        chain = prompt | structured_llm
        result = await chain.ainvoke({"message": state.message})
        
        return {
            "category": result.category,
            "department": result.department
        }
    except Exception as e:
        logger.error(f"Error in Gemini categorization: {e}. Falling back to keywords.")
        return fallback_categorize(state.message)
