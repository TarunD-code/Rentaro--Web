"""
Rentora Maintenance Service — Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
import datetime
import enum
from .database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class RequestCategory(str, enum.Enum):
    plumbing = "plumbing"
    electrical = "electrical"
    cleaning = "cleaning"
    appliance = "appliance"
    pest_control = "pest_control"
    carpentry = "carpentry"
    painting = "painting"
    other = "other"


class RequestPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class RequestStatus(str, enum.Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"
    cancelled = "cancelled"


class AssignmentStatus(str, enum.Enum):
    assigned = "assigned"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


# ── Maintenance Request ──────────────────────────────────────────────────────

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, nullable=True, index=True)
    property_id = Column(Integer, nullable=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)

    category = Column(String, nullable=False, default=RequestCategory.other.value)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    photo_urls = Column(String, nullable=True)  # Comma-separated URLs

    priority = Column(String, nullable=False, default=RequestPriority.medium.value)
    status = Column(String, nullable=False, default=RequestStatus.open.value)

    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Vendor Assignment ────────────────────────────────────────────────────────

class VendorAssignment(Base):
    __tablename__ = "vendor_assignments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, nullable=False, index=True)

    vendor_name = Column(String, nullable=False)
    vendor_phone = Column(String, nullable=True)
    vendor_email = Column(String, nullable=True)
    vendor_type = Column(String, nullable=True)  # plumber, electrician, etc.

    assigned_by = Column(String, nullable=False)  # owner/admin email
    estimated_date = Column(DateTime, nullable=True)
    actual_date = Column(DateTime, nullable=True)

    cost_estimate = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=AssignmentStatus.assigned.value)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
