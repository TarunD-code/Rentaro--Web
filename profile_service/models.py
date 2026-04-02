from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class UserProfile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_identifier = Column(String, unique=True, index=True) # matches email_or_phone from auth
    full_name = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    address = Column(String, nullable=True)
    kyc_status = Column(String, default="not_submitted") # not_submitted, pending_review, verified, rejected
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    document_type = Column(String) # aadhaar, pan, passport
    s3_url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
