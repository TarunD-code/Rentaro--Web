from pydantic import BaseModel
from typing import Optional, List
import datetime

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    photo_url: Optional[str] = None

class KYCDocumentOut(BaseModel):
    id: int
    document_type: str
    s3_url: str
    uploaded_at: datetime.datetime
    
    model_config = {"from_attributes": True}

class ProfileOut(BaseModel):
    id: int
    user_identifier: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    email: Optional[str]
    date_of_birth: Optional[str]
    age: Optional[int]
    phone_number: Optional[str]
    address: Optional[str]
    permanent_address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    photo_url: Optional[str]
    kyc_status: str
    documents: List[KYCDocumentOut] = []

    model_config = {"from_attributes": True}

class MessageCreate(BaseModel):
    receiver_id: str
    property_id: int
    body: str

class MessageOut(BaseModel):
    id: int
    sender_id: str
    receiver_id: str
    property_id: int
    body: str
    is_read: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class NotificationOut(BaseModel):
    id: int
    user_id: str
    type: str
    content: str
    is_read: bool
    created_at: datetime.datetime

    class Config:
        orm_mode = True
