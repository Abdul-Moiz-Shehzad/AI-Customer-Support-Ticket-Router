from typing import Optional
from pydantic import BaseModel


class TicketInput(BaseModel):
    ticket_id: Optional[str] = None
    customer_name: str
    customer_email: str
    subscription: str
    message: str


class TicketState(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: str
    subscription: str
    message: str

    category: str = ""
    priority: str = ""
    sentiment: str = ""
    escalation_required: bool = False
    department: str = ""
    kb_context: str = ""
    reply_message: str = ""
    auto_reply_sent: bool = False
    routed_to_queue: bool = False
    status: str = "pending"


class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    category: Optional[str] = ""
    priority: Optional[str] = ""
    department: Optional[str] = ""
    escalation_required: Optional[bool] = False
    reply_message: Optional[str] = ""
    auto_reply_sent: Optional[bool] = False


class TicketSubmissionResponse(BaseModel):
    ticket_id: str
    status: str
    message: str