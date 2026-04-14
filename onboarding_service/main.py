"""
Rentora Onboarding Service — FastAPI Application
Port: 8006

Handles tenant onboarding, KYC verification, digital agreement
generation, and e-signature tracking.
"""

import logging
import datetime
import hashlib
import uuid
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
import jwt

from . import models, schemas, database

# ── Config ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("onboarding_service")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Onboarding Service", version="1.0.0")


# ── Auth ─────────────────────────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════════════════
#  ONBOARDING ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/onboarding/initiate", response_model=schemas.OnboardingOut, status_code=201)
def initiate_onboarding(
    data: schemas.OnboardingInitiate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Tenant initiates onboarding with personal details."""
    # Check for existing active onboarding
    existing = db.query(models.OnboardingRecord).filter(
        models.OnboardingRecord.tenant_id == data.tenant_id,
        models.OnboardingRecord.status.notin_(["completed", "cancelled"]),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Active onboarding already exists")

    record = models.OnboardingRecord(
        tenant_id=data.tenant_id,
        property_id=data.property_id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        age=data.age,
        permanent_address=data.permanent_address,
        emergency_contact=data.emergency_contact,
        occupation=data.occupation,
        employer=data.employer,
        status=models.OnboardingStatus.documents_pending.value,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(f"Onboarding #{record.id} initiated for {data.tenant_id}")
    return record


@app.get("/onboarding/{onboarding_id}", response_model=schemas.OnboardingOut)
def get_onboarding(
    onboarding_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    record = db.query(models.OnboardingRecord).filter(
        models.OnboardingRecord.id == onboarding_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding record not found")
    return record


@app.get("/onboarding/active/me", response_model=Optional[schemas.OnboardingOut])
def get_active_onboarding(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    record = db.query(models.OnboardingRecord).filter(
        models.OnboardingRecord.tenant_id == user_info["sub"],
        models.OnboardingRecord.status.notin_(["completed", "cancelled"]),
    ).order_by(models.OnboardingRecord.created_at.desc()).first()
    if not record:
        return None
    return record


@app.put("/onboarding/{onboarding_id}/status", response_model=schemas.OnboardingOut)
def update_onboarding_status(
    onboarding_id: int,
    data: schemas.OnboardingStatusUpdate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    record = db.query(models.OnboardingRecord).filter(
        models.OnboardingRecord.id == onboarding_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    record.status = data.status
    if data.kyc_notes:
        record.kyc_notes = data.kyc_notes

    if data.status == "kyc_verified":
        record.kyc_status = "verified"
        record.verified_by = user_info["sub"]
        record.verified_at = datetime.datetime.utcnow()
    elif data.status == "kyc_rejected":
        record.kyc_status = "rejected"
    elif data.status == "completed":
        record.kyc_status = "verified"

    db.commit()
    db.refresh(record)
    logger.info(f"Onboarding #{onboarding_id} status → {data.status}")
    return record


# ══════════════════════════════════════════════════════════════════════════════
#  KYC ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/onboarding/kyc", response_model=schemas.KYCOut, status_code=201)
def upload_kyc(
    data: schemas.KYCUpload,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Upload KYC document for onboarding."""
    onboarding = db.query(models.OnboardingRecord).filter(
        models.OnboardingRecord.id == data.onboarding_id,
    ).first()
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    # Mask document number for storage
    masked_number = None
    if data.document_number:
        masked_number = "XXXX" + data.document_number[-4:] if len(data.document_number) > 4 else data.document_number

    kyc = models.OnboardingKYC(
        onboarding_id=data.onboarding_id,
        tenant_id=user_info["sub"],
        document_type=data.document_type,
        document_number=masked_number,
        file_url=data.file_url,
        status="pending",
    )
    db.add(kyc)

    # Update onboarding status
    onboarding.status = models.OnboardingStatus.kyc_submitted.value
    db.commit()
    db.refresh(kyc)

    logger.info(f"KYC uploaded: {data.document_type} for onboarding #{data.onboarding_id}")
    return kyc


@app.get("/onboarding/{onboarding_id}/kyc", response_model=List[schemas.KYCOut])
def get_kyc_documents(
    onboarding_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    return db.query(models.OnboardingKYC).filter(
        models.OnboardingKYC.onboarding_id == onboarding_id,
    ).order_by(models.OnboardingKYC.uploaded_at.desc()).all()


@app.put("/onboarding/kyc/{kyc_id}/verify", response_model=schemas.KYCOut)
def verify_kyc(
    kyc_id: int,
    data: schemas.KYCVerify,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Admin verifies or rejects a KYC document."""
    if user_info["role"] not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Only admin/owner can verify KYC")

    kyc = db.query(models.OnboardingKYC).filter(
        models.OnboardingKYC.id == kyc_id,
    ).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC document not found")

    kyc.status = data.status
    if data.rejection_reason:
        kyc.rejection_reason = data.rejection_reason

    # Update parent onboarding if all docs verified
    if data.status == "verified":
        all_kyc = db.query(models.OnboardingKYC).filter(
            models.OnboardingKYC.onboarding_id == kyc.onboarding_id,
        ).all()
        all_verified = all(k.status == "verified" for k in all_kyc)
        if all_verified:
            onboarding = db.query(models.OnboardingRecord).filter(
                models.OnboardingRecord.id == kyc.onboarding_id,
            ).first()
            if onboarding:
                onboarding.status = models.OnboardingStatus.kyc_verified.value
                onboarding.kyc_status = "verified"
                onboarding.verified_by = user_info["sub"]
                onboarding.verified_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(kyc)
    logger.info(f"KYC #{kyc_id} → {data.status}")
    return kyc


# ══════════════════════════════════════════════════════════════════════════════
#  AGREEMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/agreements/create", response_model=schemas.AgreementOut, status_code=201)
def create_agreement(
    data: schemas.AgreementCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Create a digital rental agreement."""
    doc_hash = hashlib.sha256(
        f"{data.property_id}{data.tenant_id}{data.owner_id}{datetime.datetime.utcnow()}".encode()
    ).hexdigest()[:16]

    agreement = models.DigitalAgreement(
        onboarding_id=data.onboarding_id,
        property_id=data.property_id,
        tenant_id=data.tenant_id,
        owner_id=data.owner_id,
        start_date=data.start_date,
        end_date=data.end_date,
        monthly_rent=data.monthly_rent,
        security_deposit=data.security_deposit,
        notice_period_days=data.notice_period_days,
        terms_json=data.terms_json,
        document_hash=doc_hash,
        status=models.AgreementStatus.draft.value,
    )
    db.add(agreement)
    db.commit()
    db.refresh(agreement)

    # Generate PDF
    from .agreement_pdf import generate_agreement_html
    html = generate_agreement_html(agreement)
    agreement.pdf_url = f"/onboarding/agreements/{agreement.id}/pdf"
    agreement.status = models.AgreementStatus.generated.value
    db.commit()
    db.refresh(agreement)

    logger.info(f"Agreement #{agreement.id} created: {data.tenant_id} ↔ {data.owner_id}")
    return agreement


@app.get("/agreements/{agreement_id}", response_model=schemas.AgreementOut)
def get_agreement(
    agreement_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    agreement = db.query(models.DigitalAgreement).filter(
        models.DigitalAgreement.id == agreement_id,
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return agreement


@app.get("/agreements", response_model=List[schemas.AgreementOut])
def list_agreements(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.DigitalAgreement)
    if user_info["role"] != "admin":
        query = query.filter(
            or_(
                models.DigitalAgreement.tenant_id == user_info["sub"],
                models.DigitalAgreement.owner_id == user_info["sub"],
            )
        )
    return query.order_by(models.DigitalAgreement.created_at.desc()).all()


@app.get("/agreements/{agreement_id}/pdf")
def get_agreement_pdf(
    agreement_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Return agreement as rendered HTML (PDF fallback)."""
    from fastapi.responses import HTMLResponse
    from .agreement_pdf import generate_agreement_html

    agreement = db.query(models.DigitalAgreement).filter(
        models.DigitalAgreement.id == agreement_id,
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    html = generate_agreement_html(agreement)
    return HTMLResponse(content=html)


# ══════════════════════════════════════════════════════════════════════════════
#  E-SIGNATURE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/agreements/sign", response_model=List[schemas.SignatureOut], status_code=201)
def send_for_signing(
    data: schemas.SignatureRequest,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Send agreement for e-signatures to both tenant and owner."""
    agreement = db.query(models.DigitalAgreement).filter(
        models.DigitalAgreement.id == data.agreement_id,
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    # Create signature records for both parties
    signatures = []
    for role, signer_id in [("tenant", agreement.tenant_id), ("owner", agreement.owner_id)]:
        sign_token = str(uuid.uuid4())[:8]
        sig = models.SignatureRecord(
            agreement_id=data.agreement_id,
            signer_id=signer_id,
            signer_role=role,
            sign_link=f"/onboarding/agreements/{data.agreement_id}/sign/{sign_token}",
            status=models.SignatureStatus.sent.value,
        )
        db.add(sig)
        signatures.append(sig)

    agreement.status = models.AgreementStatus.sent_for_signing.value
    agreement.docusign_envelope_id = f"ENV-{uuid.uuid4().hex[:12].upper()}"
    db.commit()

    for sig in signatures:
        db.refresh(sig)

    logger.info(f"Agreement #{data.agreement_id} sent for signing")
    return signatures


@app.get("/agreements/{agreement_id}/signatures", response_model=List[schemas.SignatureOut])
def get_signatures(
    agreement_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    return db.query(models.SignatureRecord).filter(
        models.SignatureRecord.agreement_id == agreement_id,
    ).all()


@app.post("/agreements/{agreement_id}/sign/{role}")
def sign_agreement(
    agreement_id: int,
    role: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Tenant or owner signs the agreement."""
    if role not in ["tenant", "owner"]:
        raise HTTPException(status_code=400, detail="Role must be 'tenant' or 'owner'")

    sig = db.query(models.SignatureRecord).filter(
        models.SignatureRecord.agreement_id == agreement_id,
        models.SignatureRecord.signer_role == role,
    ).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signature record not found")

    sig.status = models.SignatureStatus.signed.value
    sig.signed_at = datetime.datetime.utcnow()
    sig.ip_address = "127.0.0.1"

    # Update agreement status
    agreement = db.query(models.DigitalAgreement).filter(
        models.DigitalAgreement.id == agreement_id,
    ).first()

    if role == "tenant":
        agreement.tenant_signed_at = datetime.datetime.utcnow()
        agreement.status = models.AgreementStatus.tenant_signed.value
    else:
        agreement.owner_signed_at = datetime.datetime.utcnow()
        agreement.status = models.AgreementStatus.owner_signed.value

    # Check if both signed
    all_sigs = db.query(models.SignatureRecord).filter(
        models.SignatureRecord.agreement_id == agreement_id,
    ).all()
    if all(s.status == "signed" for s in all_sigs):
        agreement.status = models.AgreementStatus.fully_signed.value
        agreement.fully_signed_at = datetime.datetime.utcnow()

    db.commit()
    logger.info(f"Agreement #{agreement_id} signed by {role}")
    return {"detail": f"Agreement signed by {role}", "status": agreement.status}


# ══════════════════════════════════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/stats")
def get_stats(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    user_id = user_info["sub"]
    onboardings = db.query(models.OnboardingRecord)
    agreements = db.query(models.DigitalAgreement)

    if user_info["role"] != "admin":
        onboardings = onboardings.filter(models.OnboardingRecord.tenant_id == user_id)
        agreements = agreements.filter(
            or_(
                models.DigitalAgreement.tenant_id == user_id,
                models.DigitalAgreement.owner_id == user_id,
            )
        )

    return {
        "total_onboardings": onboardings.count(),
        "pending_kyc": onboardings.filter(models.OnboardingRecord.kyc_status == "pending").count(),
        "total_agreements": agreements.count(),
        "pending_signatures": agreements.filter(
            models.DigitalAgreement.status == "sent_for_signing"
        ).count(),
        "active_agreements": agreements.filter(
            models.DigitalAgreement.status.in_(["fully_signed", "active"])
        ).count(),
    }
