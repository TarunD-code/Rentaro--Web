"""
Rentora Onboarding Service — Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
import datetime
import enum
from .database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class OnboardingStatus(str, enum.Enum):
    initiated = "initiated"
    documents_pending = "documents_pending"
    kyc_submitted = "kyc_submitted"
    kyc_verified = "kyc_verified"
    kyc_rejected = "kyc_rejected"
    completed = "completed"
    cancelled = "cancelled"


class KYCDocumentType(str, enum.Enum):
    aadhaar = "aadhaar"
    pan = "pan"
    passport = "passport"
    voter_id = "voter_id"
    driving_licence = "driving_licence"


class KYCVerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class AgreementStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    sent_for_signing = "sent_for_signing"
    tenant_signed = "tenant_signed"
    owner_signed = "owner_signed"
    fully_signed = "fully_signed"
    active = "active"
    expired = "expired"
    terminated = "terminated"


class SignatureStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    viewed = "viewed"
    signed = "signed"
    declined = "declined"
    expired = "expired"


# ── Onboarding Record ───────────────────────────────────────────────────────

class OnboardingRecord(Base):
    __tablename__ = "onboarding_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    property_id = Column(Integer, nullable=True)
    agreement_id = Column(Integer, nullable=True)

    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    permanent_address = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    employer = Column(String, nullable=True)

    status = Column(String, default=OnboardingStatus.initiated.value)
    kyc_status = Column(String, default=KYCVerificationStatus.pending.value)
    kyc_notes = Column(Text, nullable=True)  # admin review notes
    verified_by = Column(String, nullable=True)  # admin who verified
    verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── KYC Document ─────────────────────────────────────────────────────────────

class OnboardingKYC(Base):
    __tablename__ = "onboarding_kyc"

    id = Column(Integer, primary_key=True, index=True)
    onboarding_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String, nullable=False)
    document_type = Column(String, nullable=False)  # aadhaar, pan, passport, etc.
    document_number = Column(String, nullable=True)  # masked number
    file_url = Column(String, nullable=True)
    status = Column(String, default=KYCVerificationStatus.pending.value)
    rejection_reason = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── Digital Agreement ────────────────────────────────────────────────────────

class DigitalAgreement(Base):
    __tablename__ = "digital_agreements"

    id = Column(Integer, primary_key=True, index=True)
    onboarding_id = Column(Integer, nullable=True, index=True)
    property_id = Column(Integer, nullable=False)
    tenant_id = Column(String, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)

    # Agreement Details
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    monthly_rent = Column(Float, nullable=False)
    security_deposit = Column(Float, nullable=False)
    notice_period_days = Column(Integer, default=30)
    terms_json = Column(Text, nullable=True)  # JSON custom terms

    # PDF & Signature
    pdf_url = Column(String, nullable=True)
    docusign_envelope_id = Column(String, nullable=True)
    document_hash = Column(String, nullable=True)

    # Status
    status = Column(String, default=AgreementStatus.draft.value)
    tenant_signed_at = Column(DateTime, nullable=True)
    owner_signed_at = Column(DateTime, nullable=True)
    fully_signed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ── Signature Tracking ───────────────────────────────────────────────────────

class SignatureRecord(Base):
    __tablename__ = "signature_records"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, nullable=False, index=True)
    signer_id = Column(String, nullable=False)  # email
    signer_role = Column(String, nullable=False)  # tenant or owner
    sign_link = Column(String, nullable=True)
    status = Column(String, default=SignatureStatus.pending.value)
    ip_address = Column(String, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
