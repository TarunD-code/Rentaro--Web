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


class PayoutStatus(str, enum.Enum):
    pending = "pending"
    processed = "processed"
    reversed = "reversed"
    cancelled = "cancelled"
    failed = "failed"


class LedgerEntryType(str, enum.Enum):
    rent_credit = "rent_credit"
    platform_fee = "platform_fee"
    tax_deduction = "tax_deduction"
    payout_debit = "payout_debit"
    refund = "refund"


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


# ── Owner Balance ───────────────────────────────────────────────────────────

class OwnerBalance(Base):
    """Tracks the running total available balance of an owner"""
    __tablename__ = "owner_balances"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, nullable=False, index=True, unique=True)
    available_balance = Column(Float, nullable=False, default=0.0)
    pending_balance = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Ledger Entry ────────────────────────────────────────────────────────────

class LedgerEntry(Base):
    """Immutable record of money movement within the system"""
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=True, index=True)
    property_id = Column(Integer, nullable=True, index=True)
    transaction_id = Column(Integer, nullable=True) # links to PaymentTransaction
    payout_id = Column(Integer, nullable=True) # links to Payout if it's a debit

    entry_type = Column(String, nullable=False, default=LedgerEntryType.rent_credit.value)
    amount = Column(Float, nullable=False) # positive for owner credits, negative for debits (fees/payouts)
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── Fee and Tax Records ─────────────────────────────────────────────────────

class FeeRecord(Base):
    """Tracks platform deductions taken from gross rent"""
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True, index=True)
    ledger_entry_id = Column(Integer, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)
    transaction_id = Column(Integer, nullable=True)
    
    fee_type = Column(String, nullable=False, default="platform_commission")
    fee_percentage = Column(Float, nullable=False, default=5.0)
    amount_deducted = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TaxRecord(Base):
    """Tracks tax (GST/TDS) applied to fees or payouts"""
    __tablename__ = "tax_records"

    id = Column(Integer, primary_key=True, index=True)
    fee_record_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
    tax_type = Column(String, nullable=False, default="GST") # GST, TDS
    tax_rate = Column(Float, nullable=False, default=18.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── Payouts (Settlement to Bank) ────────────────────────────────────────────

class Payout(Base):
    """Batch payout job sending funds to Owner's bank"""
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, nullable=False, default=PayoutStatus.pending.value)
    
    razorpay_payout_id = Column(String, nullable=True, unique=True, index=True)
    fund_account_id = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    
    initiated_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # E.g. manual request or scheduled cron
    payout_mode = Column(String, default="scheduled")
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


