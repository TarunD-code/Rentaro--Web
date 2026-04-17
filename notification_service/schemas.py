from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class NotificationBase(BaseModel):
    user_id: str
    channel: str
    type: str
    content: str
    payload: Optional[dict] = None

class NotificationOut(NotificationBase):
    id: int
    event_id: Optional[str]
    status: str
    is_read: bool
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True

class PreferenceBase(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False

class PreferenceOut(PreferenceBase):
    user_id: str
    updated_at: datetime

    class Config:
        from_attributes = True

class PreferenceUpdate(PreferenceBase):
    pass
