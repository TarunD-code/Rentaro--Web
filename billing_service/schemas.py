from pydantic import BaseModel
from typing import Optional, List
import datetime

class ProductOut(BaseModel):
    id: int
    name: str
    duration_days: int
    price_inr: float
    priority: int

    class Config:
        from_attributes = True

class CheckoutRequest(BaseModel):
    product_id: int
    property_id: int

class PurchaseOut(BaseModel):
    id: int
    owner_id: str
    property_id: int
    product_id: int
    amount: float
    transaction_status: str
    razorpay_order_id: Optional[str] = None
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
