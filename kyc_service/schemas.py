"""
Rentora KYC — Pydantic v2 Request/Response Schemas
====================================================

SECURITY POLICY:
- No schema ever exposes raw Aadhaar or PAN values in its response model.
- The webhook payload schema accepts PII only for internal processing —
  it is NEVER forwarded to the client.
- All client-facing responses use masked values only.
"""

import uuid
import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class KYCStatusEnum(str, Enum):
    """Client-facing KYC status enumeration."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


# ─────────────────────────────────────────────────────────────
# Initiation Flow
# ─────────────────────────────────────────────────────────────

class KYCInitiateResponse(BaseModel):
    """
    Response from POST /api/v1/kyc/initiate.
    
    Contains the transaction token and a simulated vendor checkout URL
    for the frontend to redirect/embed the KYC SDK.
    """
    transaction_token: str = Field(
        ..., description="Unique token identifying this KYC session"
    )
    checkout_url: str = Field(
        ..., description="Vendor-provided URL for document capture SDK"
    )
    status: KYCStatusEnum = Field(
        default=KYCStatusEnum.PENDING,
        description="Initial status after initiation"
    )
    message: str = Field(
        default="KYC verification initiated successfully",
        description="Human-readable status message"
    )


# ─────────────────────────────────────────────────────────────
# Webhook Payload (Vendor → Rentora)
# ─────────────────────────────────────────────────────────────

class KYCWebhookPayload(BaseModel):
    """
    Payload received from the KYC vendor via webhook callback.
    
    SECURITY: This schema is used ONLY for internal deserialization.
    The raw PII fields (aadhaar_number, pan_number) are encrypted
    immediately upon receipt and NEVER logged or forwarded.
    """
    transaction_token: str = Field(
        ..., description="Matches the token from /initiate"
    )
    status: str = Field(
        ..., description="VERIFIED or FAILED"
    )
    aadhaar_number: Optional[str] = Field(
        default=None,
        description="Raw Aadhaar (12 digits) — encrypted immediately, never logged"
    )
    pan_number: Optional[str] = Field(
        default=None,
        description="Raw PAN (10 chars) — encrypted immediately, never logged"
    )
    facial_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Facial liveness match score"
    )
    vendor_reference_id: Optional[str] = Field(
        default=None,
        description="Vendor's internal transaction reference"
    )


class KYCWebhookResponse(BaseModel):
    """Acknowledgement response to the vendor webhook."""
    received: bool = True
    transaction_token: str
    status: str


# ─────────────────────────────────────────────────────────────
# Status Query (Client-Facing)
# ─────────────────────────────────────────────────────────────

class KYCStatusResponse(BaseModel):
    """
    Response from GET /api/v1/kyc/status.
    
    SECURITY: Returns ONLY masked PII values. The raw decrypted
    Aadhaar/PAN are NEVER present in this response under any
    circumstance. This is enforced at the schema level.
    """
    status: KYCStatusEnum = Field(
        ..., description="Current KYC verification status"
    )
    masked_aadhaar: Optional[str] = Field(
        default=None,
        description="Masked Aadhaar: XXXX-XXXX-1234"
    )
    masked_pan: Optional[str] = Field(
        default=None,
        description="Masked PAN: XXXXXX1234"
    )
    facial_match_score: Optional[float] = Field(
        default=None,
        description="Facial liveness score (0.0 — 1.0)"
    )
    verified_at: Optional[datetime.datetime] = Field(
        default=None,
        description="Timestamp of successful verification"
    )
    message: str = Field(
        default="",
        description="Human-readable status message"
    )

    model_config = {"from_attributes": True}


class AdminKYCRecord(BaseModel):
    id: uuid.UUID
    user_id: str
    status: KYCStatusEnum
    masked_aadhaar: Optional[str] = None
    masked_pan: Optional[str] = None
    facial_match_score: Optional[float] = None
    transaction_token: Optional[str] = None
    vendor_reference_id: Optional[str] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class ReportScheduleRequest(BaseModel):
    email: str = Field(..., description="Administrator email to receive the report")
    file_format: str = Field("csv", description="File format: csv or pdf")
    immediate: bool = Field(False, description="Whether to return the report immediately or send via background task")


class ReportScheduleResponse(BaseModel):
    scheduled: bool
    message: str
    task_id: Optional[str] = None

