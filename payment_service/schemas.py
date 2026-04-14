from pydantic import BaseModel, Field
from typing import Optional, List
import datetime


# ── Deposit ──────────────────────────────────────────────────────────────────

class DepositOrderCreate(BaseModel):
    agreement_id: int
    tenant_id: str
    owner_id: str
    property_id: int
    amount: float = Field(..., gt=0, description="Deposit amount in INR")


class DepositVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    payment_method: Optional[str] = "upi"


# ── Rent ─────────────────────────────────────────────────────────────────────

class RentPaymentCreate(BaseModel):
    agreement_id: int
    tenant_id: str
    owner_id: str
    property_id: int
    amount: float = Field(..., gt=0)
    due_date: Optional[datetime.datetime] = None


class RentPaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    payment_method: Optional[str] = "upi"


# ── Auto-Pay ─────────────────────────────────────────────────────────────────

class AutoPayMandateCreate(BaseModel):
    tenant_id: str
    agreement_id: int
    property_id: int
    max_amount: float = Field(100000.0, gt=0)
    start_date: Optional[datetime.datetime] = None


class MandateOut(BaseModel):
    id: int
    tenant_id: str
    agreement_id: Optional[int]
    property_id: Optional[int]
    razorpay_subscription_id: Optional[str]
    status: str
    max_amount: float
    frequency: str
    start_date: Optional[datetime.datetime]
    end_date: Optional[datetime.datetime]
    next_charge_date: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Payment Output ───────────────────────────────────────────────────────────

class PaymentOut(BaseModel):
    id: int
    agreement_id: Optional[int]
    tenant_id: str
    owner_id: str
    property_id: Optional[int]
    transaction_type: str
    payment_method: Optional[str]
    amount: float
    currency: str
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    status: str
    due_date: Optional[datetime.datetime]
    paid_at: Optional[datetime.datetime]
    receipt_url: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Dashboard Summary ────────────────────────────────────────────────────────

class DashboardPaymentSummary(BaseModel):
    total_paid: float = 0.0
    total_pending: float = 0.0
    next_due_date: Optional[datetime.datetime] = None
    next_due_amount: float = 0.0
    autopay_active: bool = False
    recent_transactions: List[PaymentOut] = []


# ── Webhook ──────────────────────────────────────────────────────────────────

class WebhookEvent(BaseModel):
    event: str
    payload: dict


# ── Move-Out ─────────────────────────────────────────────────────────────────

class MoveOutInitiate(BaseModel):
    agreement_id: int
    tenant_id: str
    owner_id: str
    property_id: int
    reason: Optional[str] = None
    notice_period_days: int = 30


class DeductionItem(BaseModel):
    category: str  # cleaning, damages, pending_rent, other
    description: str
    amount: float = Field(..., ge=0)
    photo_url: Optional[str] = None


class MoveOutReview(BaseModel):
    moveout_id: int
    deductions: List[DeductionItem] = []
    pending_rent: float = 0.0
    cleaning_charge: float = 0.0
    damage_charge: float = 0.0
    owner_notes: Optional[str] = None
    photo_urls: List[str] = []


class MoveOutOut(BaseModel):
    id: int
    agreement_id: int
    property_id: Optional[int]
    tenant_id: str
    owner_id: str
    status: str
    notice_period_days: int
    reason: Optional[str]
    initiated_at: Optional[datetime.datetime]
    expected_vacate_date: datetime.datetime
    actual_vacate_date: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class SettlementGenerate(BaseModel):
    moveout_id: int


class SettlementOut(BaseModel):
    id: int
    moveout_id: int
    agreement_id: Optional[int]
    tenant_id: str
    owner_id: str
    deposit_amount: float
    pending_rent: float
    cleaning_charge: float
    damage_charge: float
    total_deductions: float
    refund_amount: float
    deductions_json: Optional[str]
    owner_notes: Optional[str]
    photo_urls: Optional[str]
    settlement_pdf_url: Optional[str]
    status: str
    finalized_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
