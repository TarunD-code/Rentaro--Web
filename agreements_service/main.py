from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from . import models, schemas
from .database import engine, get_db

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rentora Agreements Service")

@app.get("/templates", response_model=List[schemas.TemplateRead])
def get_templates(db: Session = Depends(get_db)):
    return db.query(models.AgreementTemplate).filter(models.AgreementTemplate.is_active == True).all()

@app.post("/draft", response_model=schemas.AgreementRead)
def create_draft(agreement: schemas.AgreementCreate, db: Session = Depends(get_db)):
    db_agreement = models.Agreement(
        agreement_key=f"AG-{uuid.uuid4().hex[:8].upper()}",
        owner_id=agreement.owner_id,
        tenant_id=agreement.tenant_id,
        property_id=agreement.property_id,
        template_id=agreement.template_id,
        payload=agreement.payload,
        status="draft"
    )
    db.add(db_agreement)
    db.commit()
    db.refresh(db_agreement)
    
    # Create Audit Log
    audit = models.AgreementAudit(
        agreement_id=db_agreement.id,
        action="created",
        actor_id=agreement.owner_id,
        details={"message": "Initial draft created via Builder"}
    )
    db.add(audit)
    db.commit()
    
    return db_agreement

@app.post("/{id}/generate-basic")
def generate_basic_pdf(id: int, db: Session = Depends(get_db)):
    agreement = db.query(models.Agreement).filter(models.Agreement.id == id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    # MOCK PDF GENERATION (Stage 1)
    mock_url = f"/static/agreements/{agreement.agreement_key}_basic.pdf"
    agreement.basic_pdf_url = mock_url
    agreement.status = "generated"
    
    db.commit()
    return {"status": "success", "pdf_url": mock_url}

@app.get("/{id}", response_model=schemas.AgreementRead)
def get_agreement(id: int, db: Session = Depends(get_db)):
    agreement = db.query(models.Agreement).filter(models.Agreement.id == id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return agreement
