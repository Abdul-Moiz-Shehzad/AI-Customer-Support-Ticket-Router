import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from app.models import TicketState
from utils.config import CLASSIFICATION_MODEL

load_dotenv()
logger = logging.getLogger(__name__)

class PrioritizationResult(BaseModel):
    priority: str = Field(description="Priority level: 'High', 'Medium', or 'Low'")
    sentiment: str = Field(description="Customer sentiment: 'positive', 'neutral', or 'negative'")

def fallback_prioritize(message: str, subscription: str) -> dict:
    msg = (message or "").lower()
    sub = (subscription or "").lower()
    import re
    words = set(re.findall(r'\w+', msg))
    
    if any(k in words for k in ["urgent", "emergency", "broken", "down", "critical", "blocking", "refund", "charge"]):
        priority = "High"
    elif any(k in words for k in ["slow", "issue", "question", "help", "problem"]):
        priority = "Medium"
    else:
        priority = "Low"
        
    if any(k in words for k in ["angry", "frustrated", "bad", "disappointed", "annoyed", "terrible", "worst", "hate"]):
        sentiment = "negative"
    elif any(k in words for k in ["thank", "great", "awesome", "good", "perfect", "love"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"
        
    escalation_required = False
    if priority == "High" or sentiment == "negative" or sub in ["enterprise", "premium"]:
        escalation_required = True
        
    return {
        "priority": priority,
        "sentiment": sentiment,
        "escalation_required": escalation_required
    }

async def prioritize_ticket(state: TicketState) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key found. Using keyword fallback for prioritization.")
        return fallback_prioritize(state.message, state.subscription)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatGoogleGenerativeAI(model=CLASSIFICATION_MODEL, google_api_key=api_key)
        structured_llm = llm.with_structured_output(PrioritizationResult)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert customer support agent. Analyze the customer support ticket message to decide its priority and customer sentiment."),
            ("human", "Ticket Message:\n{message}\n\nSelect priority from:\n- High (for critical issues, blocking bugs, or urgent refund requests)\n- Medium (for standard bugs, service issues, or general questions)\n- Low (for feature requests, minor feedback, or simple inquiries)\n\nSelect sentiment from:\n- positive (happy, satisfied, or thanking the support team)\n- neutral (standard inquiries or descriptions of issues without strong emotion)\n- negative (frustrated, angry, disappointed, or highly critical)")
        ])

        chain = prompt | structured_llm
        result = await chain.ainvoke({"message": state.message})
        
        priority = result.priority
        sentiment = result.sentiment
        
        # Escalation rules
        sub = (state.subscription or "").lower()
        escalation_required = False
        if priority == "High" or sentiment == "negative" or sub in ["enterprise", "premium"]:
            escalation_required = True
            
        return {
            "priority": priority,
            "sentiment": sentiment,
            "escalation_required": escalation_required
        }
    except Exception as e:
        logger.error(f"Error in Gemini prioritization: {e}. Falling back to keywords.")
        return fallback_prioritize(state.message, state.subscription)
