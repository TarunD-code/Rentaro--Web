from sqlalchemy import Column, Integer, String, Boolean, DateTime
import datetime
from .database import Base

class NotificationToken(Base):
    __tablename__ = "notification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # Matches user_identifier (email/phone) from auth
    device_token = Column(String, unique=True, index=True)
    platform = Column(String) # "ios", "android", "web"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class NotificationHistory(Base):
    """Stores the history of sent push notifications."""
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    type = Column(String) # "message", "alert", etc.
    title = Column(String, nullable=True)
    message = Column(String, nullable=True)
    content = Column(String, nullable=True)
    data_json = Column(String, nullable=True) # Extra metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, nullable=True) # "success", "failed"
    is_read = Column(Boolean, default=False)
