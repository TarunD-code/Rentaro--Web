from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email_or_phone: str
    password: str
    role: str # "tenant" | "owner" | "admin"

class UserOut(BaseModel):
    id: int
    email_or_phone: str
    role: str
    is_verified: bool

    model_config = {"from_attributes": True}

class OTPVerify(BaseModel):
    email_or_phone: str
    otp: str

class UserLogin(BaseModel):
    email_or_phone: str
    password: str
    role: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
