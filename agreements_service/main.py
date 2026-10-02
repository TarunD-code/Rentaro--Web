from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from . import models, schemas
from .database import engine, get_db

from fastapi.middleware.cors import CORSMiddleware

# Initialize database
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="Rentora Agreements Service")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

def get_current_user_info(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        role: str = payload.get("role")
        if user_identifier is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"sub": user_identifier, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
    
    # Generate Real PDF
    # Ensure static directory exists
    os.makedirs(f"frontend/public/static/agreements", exist_ok=True)
    file_path = f"frontend/public/static/agreements/{agreement.agreement_key}_basic.pdf"
    
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1 * inch, height - 1 * inch, "Rental Agreement")
    
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.5 * inch, f"Agreement ID: {agreement.agreement_key}")
    c.drawString(1 * inch, height - 1.8 * inch, f"Owner ID: {agreement.owner_id}")
    c.drawString(1 * inch, height - 2.1 * inch, f"Tenant ID: {agreement.tenant_id}")
    c.drawString(1 * inch, height - 2.4 * inch, f"Property ID: {agreement.property_id}")
    
    y = height - 3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Terms and Conditions")
    y -= 0.3 * inch
    c.setFont("Helvetica", 10)
    
    # Safely get payload
    payload = agreement.payload or {}
    
    # Custom Clauses rendering
    custom_clauses = payload.get("custom_clauses", [])
    if custom_clauses:
        for idx, clause in enumerate(custom_clauses, start=1):
            text = f"{idx}. {clause.get('title', 'Clause')}: {clause.get('text', '')}"
            c.drawString(1 * inch, y, text)
            y -= 0.3 * inch
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 10)
    else:
        c.drawString(1 * inch, y, "1. Standard Rentora terms apply.")
        y -= 0.3 * inch
    
    c.save()
    
    mock_url = f"/static/agreements/{agreement.agreement_key}_basic.pdf"
    agreement.basic_pdf_url = mock_url
    agreement.status = "generated"
    
    db.commit()
    return {"status": "success", "pdf_url": mock_url}

@app.get("/user/list", response_model=List[schemas.AgreementRead])
def list_user_agreements(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    if user_info["role"] == "admin":
        return db.query(models.Agreement).all()
    return db.query(models.Agreement).filter(
        (models.Agreement.tenant_id == user_info["sub"]) | 
        (models.Agreement.owner_id == user_info["sub"])
    ).all()

@app.get("/{id}", response_model=schemas.AgreementRead)
def get_agreement(id: int, db: Session = Depends(get_db)):
    agreement = db.query(models.Agreement).filter(models.Agreement.id == id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return agreement
