from pydantic import BaseModel
from typing import Optional, List
import datetime

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None

class KYCDocumentOut(BaseModel):
    id: int
    document_type: str
    s3_url: str
    uploaded_at: datetime.datetime
    
    class Config:
        orm_mode = True

class ProfileOut(BaseModel):
    id: int
    user_identifier: str
    full_name: Optional[str]
    date_of_birth: Optional[str]
    address: Optional[str]
    kyc_status: str
    documents: List[KYCDocumentOut] = []

    class Config:
        orm_mode = True
