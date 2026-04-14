from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class UserProfile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_identifier = Column(String, unique=True, index=True) # matches email_or_phone from auth
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    permanent_address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    kyc_status = Column(String, default="not_submitted") # not_submitted, pending_review, verified, rejected
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    document_type = Column(String) # aadhaar, pan, passport
    s3_url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String, index=True) # user_identifier
    receiver_id = Column(String, index=True) # user_identifier
    property_id = Column(Integer, index=True)
    body = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # user_identifier
    type = Column(String) # "message", "inquiry", "kyc", "favorite"
    content = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
