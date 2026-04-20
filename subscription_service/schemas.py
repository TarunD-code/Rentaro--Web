from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SubscriptionBase(BaseModel):
    plan_key: str

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionOut(SubscriptionBase):
    id: int
    tenant_id: str
    provider_subscription_id: str
    status: str
    current_period_end: datetime

    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    id: int
    subscription_id: int
    amount_cents: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConciergeBase(BaseModel):
    property_id: Optional[int]
    request_type: str
    details: str

class ConciergeCreate(ConciergeBase):
    pass

class ConciergeOut(ConciergeBase):
    id: int
    tenant_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
