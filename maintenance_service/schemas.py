"""
Rentora Maintenance Service — Pydantic Schemas
"""

import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────────────

class MaintenanceRequestCreate(BaseModel):
    agreement_id: Optional[int] = None
    property_id: int
    tenant_id: str
    owner_id: str
    category: str = "other"
    title: str
    description: Optional[str] = None
    photo_urls: List[str] = []
    priority: str = "medium"


class MaintenanceRequestOut(BaseModel):
    id: int
    agreement_id: Optional[int]
    property_id: Optional[int]
    tenant_id: str
    owner_id: str
    category: str
    title: str
    description: Optional[str]
    photo_urls: Optional[str]
    priority: str
    status: str
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime.datetime]
    closed_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class StatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


# ── Assignment Schemas ───────────────────────────────────────────────────────

class VendorAssignmentCreate(BaseModel):
    request_id: int
    vendor_name: str
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_type: Optional[str] = None
    estimated_date: Optional[datetime.datetime] = None
    cost_estimate: Optional[float] = None
    notes: Optional[str] = None


class VendorAssignmentOut(BaseModel):
    id: int
    request_id: int
    vendor_name: str
    vendor_phone: Optional[str]
    vendor_email: Optional[str]
    vendor_type: Optional[str]
    assigned_by: str
    estimated_date: Optional[datetime.datetime]
    actual_date: Optional[datetime.datetime]
    cost_estimate: Optional[float]
    actual_cost: Optional[float]
    notes: Optional[str]
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AssignmentStatusUpdate(BaseModel):
    status: str
    actual_cost: Optional[float] = None
    notes: Optional[str] = None
