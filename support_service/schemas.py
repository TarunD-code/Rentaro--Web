from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TicketBase(BaseModel):
    subject: str
    description: str

class TicketCreate(TicketBase):
    pass

class TicketOut(TicketBase):
    id: int
    tenant_id: str
    status: str
    priority: str
    is_premium: bool
    sla_hours: int
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketUpdateCreate(BaseModel):
    message: str

class TicketUpdateOut(BaseModel):
    id: int
    ticket_id: int
    author_id: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
