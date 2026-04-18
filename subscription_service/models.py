from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True) # References user_identifier
    plan_key = Column(String, nullable=False) # e.g., 'monthly_premium', 'yearly_vip'
    provider_subscription_id = Column(String, unique=True, nullable=True)
    status = Column(String, default="active") # active, past_due, canceled, trialing
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    provider_invoice_id = Column(String, unique=True, nullable=True)
    amount_cents = Column(Integer)
    currency = Column(String, default="INR")
    status = Column(String) # paid, pending, failed
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    pdf_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ConciergeRequest(Base):
    __tablename__ = "concierge_requests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    property_id = Column(Integer, index=True, nullable=True)
    request_type = Column(String) # viewing, shortlist, booking, custom
    details = Column(JSON, nullable=True)
    status = Column(String, default="pending") # pending, in_progress, completed, canceled
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
