from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email_or_phone: str
    password: str
    role: str # "tenant" | "owner"

class UserOut(BaseModel):
    id: int
    email_or_phone: str
    role: str
    is_verified: bool

    class Config:
        orm_mode = True

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
