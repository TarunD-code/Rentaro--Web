import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from .database import Base

class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(Integer, primary_key=True, index=True)
    agreement_key = Column(String, unique=True, index=True) # UUID or human-readable key
    owner_id = Column(String, index=True) 
    tenant_id = Column(String, index=True)
    property_id = Column(Integer, index=True)
    status = Column(String, default="draft") # draft, generated, sent, signed, archived
    template_id = Column(String, nullable=True)
    version = Column(Integer, default=1)
    
    payload = Column(JSON, nullable=True) # Full state of clauses/terms
    
    basic_pdf_url = Column(String, nullable=True)
    branded_pdf_url = Column(String, nullable=True)
    document_hash = Column(String, nullable=True)
    
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    audit_logs = relationship("AgreementAudit", back_populates="agreement", cascade="all, delete-orphan")
    line_items = relationship("AgreementLineItem", back_populates="agreement", cascade="all, delete-orphan")
    signatures = relationship("AgreementSignature", back_populates="agreement", cascade="all, delete-orphan")

class AgreementTemplate(Base):
    __tablename__ = "agreement_templates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    clauses = Column(JSON) # Array of clause objects
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgreementLineItem(Base):
    __tablename__ = "agreement_line_items"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, ForeignKey("agreements.id"))
    label = Column(String)
    amount = Column(Float)
    is_editable = Column(Boolean, default=True)
    
    agreement = relationship("Agreement", back_populates="line_items")

class AgreementSignature(Base):
    __tablename__ = "agreement_signatures"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, ForeignKey("agreements.id"))
    signer_id = Column(String, index=True)
    signer_role = Column(String) # owner, tenant, witness
    signature_type = Column(String, default="OTP") # OTP, e-sign, physical
    signed_at = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String, nullable=True)
    
    agreement = relationship("Agreement", back_populates="signatures")

class AgreementAudit(Base):
    __tablename__ = "agreement_audit"

    id = Column(Integer, primary_key=True, index=True)
    agreement_id = Column(Integer, ForeignKey("agreements.id"))
    action = Column(String) # created, updated, generated, sent, signed
    actor_id = Column(String)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    agreement = relationship("Agreement", back_populates="audit_logs")
