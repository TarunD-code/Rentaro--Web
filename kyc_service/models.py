"""
Rentora KYC — SQLAlchemy Models with Hybrid Encryption Attributes
=================================================================

The KYCRecord model uses SQLAlchemy hybrid properties to provide
transparent encryption/decryption of Aadhaar and PAN numbers.

Writing `record.aadhaar_number = "123456781234"` will:
  1. Encrypt the value into `encrypted_aadhaar` (LargeBinary column)
  2. Compute and store `masked_aadhaar` as "XXXX-XXXX-1234"

Reading `record.aadhaar_number` will:
  1. Decrypt `encrypted_aadhaar` and return the plaintext

The raw encrypted columns are never directly exposed through API responses.
"""

import uuid
import datetime
from sqlalchemy import (
    Column, String, Float, LargeBinary, DateTime,
    Enum as SQLEnum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base
from .encryption import cipher_engine

import enum


class KYCStatus(str, enum.Enum):
    """KYC verification lifecycle states."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class KYCRecord(Base):
    """
    Core KYC verification record.
    
    SECURITY INVARIANTS:
    - `encrypted_aadhaar` and `encrypted_pan` are NEVER returned in API responses.
    - Only `masked_aadhaar` and `masked_pan` are exposed via the status endpoint.
    - The hybrid properties `aadhaar_number` / `pan_number` exist solely for
      internal service logic (e.g., webhook processing, audit).
    - All database writes go through the setter which enforces encryption.
    """

    __tablename__ = "kyc_records"

    # ── Primary Key ──────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique KYC record identifier (UUIDv4)"
    )

    # ── User Reference ───────────────────────────────────────
    user_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="References auth.users.email_or_phone"
    )

    # ── Verification Status ──────────────────────────────────
    status = Column(
        SQLEnum(KYCStatus, name="kyc_status_enum", schema="kyc"),
        nullable=False,
        default=KYCStatus.PENDING,
        comment="Current verification lifecycle state"
    )

    # ── Masked Values (Safe for API exposure) ────────────────
    masked_aadhaar = Column(
        String(16),
        nullable=True,
        comment="Masked Aadhaar: XXXX-XXXX-1234"
    )
    masked_pan = Column(
        String(14),
        nullable=True,
        comment="Masked PAN: XXXXXX1234"
    )

    # ── Encrypted PII (NEVER exposed in API responses) ───────
    encrypted_aadhaar = Column(
        LargeBinary,
        nullable=True,
        comment="Fernet-encrypted Aadhaar number"
    )
    encrypted_pan = Column(
        LargeBinary,
        nullable=True,
        comment="Fernet-encrypted PAN number"
    )

    # ── Biometric Score ──────────────────────────────────────
    facial_match_score = Column(
        Float,
        nullable=True,
        default=None,
        comment="Facial liveness/match score (0.0 - 1.0)"
    )

    # ── Transaction Tracking ─────────────────────────────────
    transaction_token = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Unique token per KYC initiation session"
    )

    # ── Vendor Reference ─────────────────────────────────────
    vendor_reference_id = Column(
        String(255),
        nullable=True,
        comment="External vendor transaction/reference ID"
    )

    # ── Timestamps ───────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.utcnow,
        comment="Record creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="Last modification timestamp"
    )

    # ─────────────────────────────────────────────────────────
    # Hybrid Properties — Transparent Encryption/Decryption
    # ─────────────────────────────────────────────────────────
    #
    # These properties provide a clean Python API:
    #   record.aadhaar_number = "123456781234"  → encrypts + masks
    #   value = record.aadhaar_number            → decrypts
    #
    # SECURITY: The plaintext NEVER touches the database. Only
    # encrypted bytes are stored in the `encrypted_*` columns.
    # ─────────────────────────────────────────────────────────

    @hybrid_property
    def aadhaar_number(self) -> str | None:
        """Decrypt and return the Aadhaar number from encrypted storage."""
        if not self.encrypted_aadhaar:
            return None
        try:
            return cipher_engine.decrypt(self.encrypted_aadhaar)
        except Exception:
            return None

    @aadhaar_number.setter
    def aadhaar_number(self, value: str):
        """Encrypt Aadhaar and compute masked representation."""
        if value:
            self.encrypted_aadhaar = cipher_engine.encrypt(value)
            self.masked_aadhaar = cipher_engine.mask_aadhaar(value)
        else:
            self.encrypted_aadhaar = None
            self.masked_aadhaar = None

    @hybrid_property
    def pan_number(self) -> str | None:
        """Decrypt and return the PAN number from encrypted storage."""
        if not self.encrypted_pan:
            return None
        try:
            return cipher_engine.decrypt(self.encrypted_pan)
        except Exception:
            return None

    @pan_number.setter
    def pan_number(self, value: str):
        """Encrypt PAN and compute masked representation."""
        if value:
            self.encrypted_pan = cipher_engine.encrypt(value)
            self.masked_pan = cipher_engine.mask_pan(value)
        else:
            self.encrypted_pan = None
            self.masked_pan = None

    def __repr__(self):
        return (
            f"<KYCRecord(id={self.id}, user_id='{self.user_id}', "
            f"status={self.status}, masked_aadhaar='{self.masked_aadhaar}')>"
        )
