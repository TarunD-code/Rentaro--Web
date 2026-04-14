"""
Rentora Onboarding Service — Pydantic Schemas
"""

import datetime
from typing import Optional, List
from pydantic import BaseModel


# ── Onboarding ───────────────────────────────────────────────────────────────

class OnboardingInitiate(BaseModel):
    tenant_id: str
    property_id: Optional[int] = None
    full_name: str
    email: str
    phone: str
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    permanent_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None


class OnboardingOut(BaseModel):
    id: int
    tenant_id: str
    property_id: Optional[int]
    agreement_id: Optional[int]
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    date_of_birth: Optional[str]
    age: Optional[int]
    permanent_address: Optional[str]
    emergency_contact: Optional[str]
    occupation: Optional[str]
    employer: Optional[str]
    status: str
    kyc_status: str
    kyc_notes: Optional[str]
    verified_by: Optional[str]
    verified_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class OnboardingStatusUpdate(BaseModel):
    status: str
    kyc_notes: Optional[str] = None


# ── KYC ──────────────────────────────────────────────────────────────────────

class KYCUpload(BaseModel):
    onboarding_id: int
    document_type: str  # aadhaar, pan, passport, etc.
    document_number: Optional[str] = None
    file_url: Optional[str] = None


class KYCOut(BaseModel):
    id: int
    onboarding_id: int
    tenant_id: str
    document_type: str
    document_number: Optional[str]
    file_url: Optional[str]
    status: str
    rejection_reason: Optional[str]
    uploaded_at: datetime.datetime

    model_config = {"from_attributes": True}


class KYCVerify(BaseModel):
    status: str  # verified or rejected
    rejection_reason: Optional[str] = None


# ── Agreement ────────────────────────────────────────────────────────────────

class AgreementCreate(BaseModel):
    onboarding_id: Optional[int] = None
    property_id: int
    tenant_id: str
    owner_id: str
    start_date: str
    end_date: str
    monthly_rent: float
    security_deposit: float
    notice_period_days: int = 30
    terms_json: Optional[str] = None


class AgreementOut(BaseModel):
    id: int
    onboarding_id: Optional[int]
    property_id: int
    tenant_id: str
    owner_id: str
    start_date: Optional[str]
    end_date: Optional[str]
    monthly_rent: float
    security_deposit: float
    notice_period_days: int
    terms_json: Optional[str]
    pdf_url: Optional[str]
    docusign_envelope_id: Optional[str]
    status: str
    tenant_signed_at: Optional[datetime.datetime]
    owner_signed_at: Optional[datetime.datetime]
    fully_signed_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class SignatureRequest(BaseModel):
    agreement_id: int


class SignatureOut(BaseModel):
    id: int
    agreement_id: int
    signer_id: str
    signer_role: str
    sign_link: Optional[str]
    status: str
    signed_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
