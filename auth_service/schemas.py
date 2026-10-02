from pydantic import BaseModel, field_validator
from typing import Optional

ALLOWED_PUBLIC_ROLES = {"tenant", "owner"}

class UserCreate(BaseModel):
    email_or_phone: str
    password: str
    role: str  # "tenant" | "owner" only — "admin" is rejected at validation

    @field_validator("role")
    @classmethod
    def role_must_be_public(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised not in ALLOWED_PUBLIC_ROLES:
            raise ValueError(
                f"Role '{v}' cannot be self-assigned via public registration. "
                "Allowed roles: tenant, owner."
            )
        return normalised

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
