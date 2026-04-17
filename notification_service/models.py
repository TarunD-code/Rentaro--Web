from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, BigInteger
from sqlalchemy.sql import func
from .database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True) # From Kafka event
    user_id = Column(String, index=True, nullable=False) # user_identifier from JWT
    channel = Column(String, index=True) # 'push', 'email', 'sms'
    type = Column(String, index=True) # 'rent.due', 'message.received', etc.
    content = Column(String, nullable=False)
    payload = Column(JSON, nullable=True) # Full event data
    status = Column(String, default="pending") # pending, sent, failed, read
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id = Column(String, primary_key=True, index=True)
    push_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
