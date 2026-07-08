from pydantic import BaseModel


class TicketInput(BaseModel):
    ticket_id: str
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

    category: str
    priority: str
    sentiment: str
    escalation_required: bool


class TicketResponse(BaseModel):
    ticket_id: str
    category: str
    priority: str
    department: str
    escalation_required: bool