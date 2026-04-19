from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class TemplateBase(BaseModel):
    id: str
    name: str
    description: str
    clauses: List[Any]

class TemplateRead(TemplateBase):
    class Config:
        from_attributes = True

class AgreementBase(BaseModel):
    owner_id: str
    tenant_id: str
    property_id: int
    template_id: Optional[str] = None
    payload: Any

class AgreementCreate(AgreementBase):
    pass

class AgreementRead(BaseModel):
    id: int
    agreement_key: str
    owner_id: str
    tenant_id: str
    property_id: int
    status: str
    version: int
    payload: Optional[Any]
    basic_pdf_url: Optional[str]
    branded_pdf_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
