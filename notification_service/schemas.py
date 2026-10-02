from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TokenRegister(BaseModel):
    device_token: str
    platform: str # ios, android, web

class TokenOut(BaseModel):
    id: int
    user_id: str
    device_token: str
    platform: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    body: str
    data: Optional[dict] = None

class NotificationOut(BaseModel):
    id: int
    user_id: str
    type: str
    title: Optional[str] = None
    message: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime
    status: Optional[str] = None
    is_read: bool

    class Config:
        from_attributes = True

class HealthOut(BaseModel):
    status: str
    timestamp: datetime
