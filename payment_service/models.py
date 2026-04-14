from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
import datetime
import enum
from .database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class TransactionType(str, enum.Enum):
    deposit = "deposit"
    rent = "rent"
    refund = "refund"
    settlement = "settlement"


class PaymentMethod(str, enum.Enum):
    upi = "upi"
    card = "card"
    netbanking = "netbanking"
    mandate = "mandate"
    wallet = "wallet"


class TransactionStatus(str, enum.Enum):
    created = "created"
    authorized = "authorized"
    captured = "captured"
    failed = "failed"
    refunded = "refunded"


class MandateStatus(str, enum.Enum):
    created = "created"
    authenticated = "authenticated"
    active = "active"
    paused = "paused"
    cancelled = "cancelled"
    expired = "expired"


class MoveOutStatus(str, enum.Enum):
    initiated = "initiated"
    notice_period = "notice_period"
    owner_review = "owner_review"
    settlement_pending = "settlement_pending"
    completed = "completed"
    cancelled = "cancelled"


class SettlementStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"
    paid = "paid"


# ── Payment Transaction ─────────────────────────────────────────────────────

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, nullable=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)
    property_id = Column(Integer, nullable=True, index=True)

    transaction_type = Column(String, nullable=False, default=TransactionType.rent.value)
    payment_method = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")

    razorpay_order_id = Column(String, nullable=True, unique=True, index=True)
    razorpay_payment_id = Column(String, nullable=True, unique=True)
    razorpay_signature = Column(String, nullable=True)

    status = Column(String, nullable=False, default=TransactionStatus.created.value)
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    receipt_url = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Auto-Pay Mandate ────────────────────────────────────────────────────────

class AutoPayMandate(Base):
    __tablename__ = "autopay_mandates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    agreement_id = Column(Integer, nullable=True, index=True)
    property_id = Column(Integer, nullable=True)

    razorpay_subscription_id = Column(String, nullable=True, unique=True)
    razorpay_mandate_id = Column(String, nullable=True)

    status = Column(String, nullable=False, default=MandateStatus.created.value)
    max_amount = Column(Float, nullable=False, default=100000.0)
    frequency = Column(String, default="monthly")

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    next_charge_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Move-Out Request ────────────────────────────────────────────────────────

class MoveOutRequest(Base):
    __tablename__ = "moveout_requests"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, nullable=False, index=True)
    property_id = Column(Integer, nullable=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)

    status = Column(String, nullable=False, default=MoveOutStatus.initiated.value)
    notice_period_days = Column(Integer, default=30)
    reason = Column(String, nullable=True)

    initiated_at = Column(DateTime, default=datetime.datetime.utcnow)
    expected_vacate_date = Column(DateTime, nullable=False)
    actual_vacate_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Settlement Record ───────────────────────────────────────────────────────

class SettlementRecord(Base):
    __tablename__ = "settlement_records"

    id = Column(Integer, primary_key=True, index=True)
    moveout_id = Column(Integer, nullable=False, index=True)
    agreement_id = Column(Integer, nullable=True)
    tenant_id = Column(String, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)

    deposit_amount = Column(Float, nullable=False, default=0.0)
    pending_rent = Column(Float, default=0.0)
    cleaning_charge = Column(Float, default=0.0)
    damage_charge = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0)

    deductions_json = Column(String, nullable=True)  # JSON array of deduction items
    owner_notes = Column(String, nullable=True)
    photo_urls = Column(String, nullable=True)  # Comma-separated photo URLs

    settlement_pdf_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default=SettlementStatus.draft.value)
    finalized_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

