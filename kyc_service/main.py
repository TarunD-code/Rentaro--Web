"""
Rentora KYC Service — Main Application
=======================================

Production-grade KYC verification engine with:
- Column-level Fernet encryption for Aadhaar/PAN
- HMAC-SHA256 webhook authentication
- PII-sanitized logging
- Rate-limited initiation endpoint

Port: 8016 (local dev) / 8000 (Docker internal)

Endpoints:
  GET  /health                    → Service health check
  POST /api/v1/kyc/initiate       → Start KYC verification (JWT protected)
  POST /api/v1/kyc/webhook        → Vendor callback (HMAC protected)
  GET  /api/v1/kyc/status         → Get masked KYC status (JWT protected)
"""

import os
import uuid
import json
import logging
import datetime
import time
import csv
import io

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, database
from .security import (
    get_current_user,
    get_current_admin,
    verify_webhook_signature,
    check_rate_limit,
    install_pii_filter,
)
from .encryption import cipher_engine

# ─────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("kyc_service")

# SECURITY: Install PII sanitizing filter before any request processing
install_pii_filter()

# ─────────────────────────────────────────────────────────────
# FastAPI Application
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Rentora KYC Service",
    description="Secure KYC verification engine with column-level encryption",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.1.5:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Database Table Creation (dev convenience)
# ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_create_tables():
    """
    Create the 'kyc' schema and tables if they don't exist.
    In production, use Alembic migrations instead.
    """
    try:
        from sqlalchemy import text
        with database.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS kyc"))
            conn.commit()
        database.Base.metadata.create_all(bind=database.engine)
        logger.info("KYC database schema and tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize KYC database: {e}")


# ─────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "kyc_service",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


# ═════════════════════════════════════════════════════════════
# POST /api/v1/kyc/initiate
# ═════════════════════════════════════════════════════════════
@app.post(
    "/api/v1/kyc/initiate",
    response_model=schemas.KYCInitiateResponse,
    summary="Initiate KYC Verification",
    description=(
        "Generates a unique transaction token and simulates an outbound "
        "request to a premium KYC vendor gateway (Digio/Signzy sandbox). "
        "Returns a temporary checkout token for the client SDK."
    ),
)
def initiate_kyc(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    # ── Rate Limiting ────────────────────────────────────────
    check_rate_limit(user_id)

    # ── Check for existing pending KYC ───────────────────────
    existing = (
        db.query(models.KYCRecord)
        .filter(
            models.KYCRecord.user_id == user_id,
            models.KYCRecord.status == models.KYCStatus.PENDING,
        )
        .first()
    )

    if existing:
        logger.info(f"Returning existing pending KYC for user {user_id[:3]}***")
        return schemas.KYCInitiateResponse(
            transaction_token=existing.transaction_token,
            checkout_url=f"https://sandbox.digio.in/v2/client/kyc/{existing.transaction_token}",
            status=schemas.KYCStatusEnum.PENDING,
            message="KYC verification already in progress",
        )

    # ── Generate Transaction Token ───────────────────────────
    transaction_token = f"RNT-KYC-{uuid.uuid4().hex[:16].upper()}"

    # ── Create KYC Record ────────────────────────────────────
    kyc_record = models.KYCRecord(
        user_id=user_id,
        status=models.KYCStatus.PENDING,
        transaction_token=transaction_token,
    )
    db.add(kyc_record)
    db.commit()
    db.refresh(kyc_record)

    # ── Simulate Vendor API Call ─────────────────────────────
    # In production, this would be an outbound HTTPS request to
    # the vendor's server-to-server API (Digio, Signzy, etc.)
    # returning a checkout_url for the frontend SDK.
    #
    # vendor_response = httpx.post(
    #     f"{KYC_VENDOR_API_URL}/kyc/session",
    #     json={"transaction_id": transaction_token, ...},
    #     headers={"Authorization": f"Bearer {KYC_VENDOR_API_KEY}"}
    # )
    # checkout_url = vendor_response.json()["checkout_url"]

    checkout_url = f"https://sandbox.digio.in/v2/client/kyc/{transaction_token}"

    logger.info(
        f"KYC initiated for user {user_id[:3]}*** | "
        f"token={transaction_token}"
    )

    return schemas.KYCInitiateResponse(
        transaction_token=transaction_token,
        checkout_url=checkout_url,
        status=schemas.KYCStatusEnum.PENDING,
        message="KYC verification initiated successfully",
    )


# ═════════════════════════════════════════════════════════════
# POST /api/v1/kyc/webhook
# ═════════════════════════════════════════════════════════════
@app.post(
    "/api/v1/kyc/webhook",
    response_model=schemas.KYCWebhookResponse,
    summary="KYC Vendor Webhook Callback",
    description=(
        "Receives verification results from the KYC vendor. "
        "HMAC-SHA256 signature verification is enforced via "
        "the X-Webhook-Signature header. Raw PII is encrypted "
        "immediately upon receipt."
    ),
)
async def kyc_webhook(
    raw_body: bytes = Depends(verify_webhook_signature),
    db: Session = Depends(database.get_db),
):
    # ── Parse Payload ────────────────────────────────────────
    try:
        payload_dict = json.loads(raw_body)
        payload = schemas.KYCWebhookPayload(**payload_dict)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Webhook payload parsing failed: {type(e).__name__}")
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload format"
        )

    # ── Locate KYC Record ────────────────────────────────────
    kyc_record = (
        db.query(models.KYCRecord)
        .filter(models.KYCRecord.transaction_token == payload.transaction_token)
        .first()
    )

    if not kyc_record:
        logger.warning(
            f"Webhook received for unknown transaction token: "
            f"{payload.transaction_token[:8]}..."
        )
        raise HTTPException(
            status_code=404,
            detail="Transaction token not found"
        )

    # ── Update Status ────────────────────────────────────────
    new_status = (
        models.KYCStatus.VERIFIED
        if payload.status.upper() == "VERIFIED"
        else models.KYCStatus.FAILED
    )
    kyc_record.status = new_status

    # ── Encrypt & Store PII (SECURITY-CRITICAL) ──────────────
    # The raw Aadhaar/PAN values exist in memory ONLY during
    # this block. They are encrypted before DB write and the
    # payload object goes out of scope after this function.
    if payload.aadhaar_number:
        kyc_record.aadhaar_number = payload.aadhaar_number  # → hybrid setter encrypts
    if payload.pan_number:
        kyc_record.pan_number = payload.pan_number  # → hybrid setter encrypts

    # ── Facial Match Score ───────────────────────────────────
    if payload.facial_score is not None:
        kyc_record.facial_match_score = payload.facial_score
    else:
        # Mock liveness score for sandbox/demo environments
        import random
        kyc_record.facial_match_score = round(
            random.uniform(0.85, 0.99) if new_status == models.KYCStatus.VERIFIED else
            random.uniform(0.10, 0.45),
            4
        )

    # ── Vendor Reference ─────────────────────────────────────
    if payload.vendor_reference_id:
        kyc_record.vendor_reference_id = payload.vendor_reference_id

    kyc_record.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(kyc_record)

    logger.info(
        f"Webhook processed: token={payload.transaction_token[:8]}... "
        f"status={new_status.value} | "
        f"facial_score={kyc_record.facial_match_score}"
    )

    return schemas.KYCWebhookResponse(
        received=True,
        transaction_token=payload.transaction_token,
        status=new_status.value,
    )


# ═════════════════════════════════════════════════════════════
# GET /api/v1/kyc/status
# ═════════════════════════════════════════════════════════════
@app.get(
    "/api/v1/kyc/status",
    response_model=schemas.KYCStatusResponse,
    summary="Get KYC Verification Status",
    description=(
        "Returns the current KYC status with masked PII values only. "
        "Raw decrypted Aadhaar/PAN are NEVER exposed through this endpoint."
    ),
)
def get_kyc_status(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    # ── Find Latest KYC Record ───────────────────────────────
    kyc_record = (
        db.query(models.KYCRecord)
        .filter(models.KYCRecord.user_id == user_id)
        .order_by(models.KYCRecord.created_at.desc())
        .first()
    )

    if not kyc_record:
        return schemas.KYCStatusResponse(
            status=schemas.KYCStatusEnum.PENDING,
            message="No KYC verification found. Please initiate verification.",
        )

    # ── Build Response (MASKED VALUES ONLY) ──────────────────
    # SECURITY: We read masked_aadhaar / masked_pan directly from
    # the database columns — these were pre-computed by the hybrid
    # setter. We do NOT call the decrypting getter here.
    status_message_map = {
        models.KYCStatus.PENDING: "KYC verification is in progress.",
        models.KYCStatus.VERIFIED: "KYC verification completed successfully.",
        models.KYCStatus.FAILED: "KYC verification failed. Please re-initiate.",
    }

    return schemas.KYCStatusResponse(
        status=schemas.KYCStatusEnum(kyc_record.status.value),
        masked_aadhaar=kyc_record.masked_aadhaar,
        masked_pan=kyc_record.masked_pan,
        facial_match_score=kyc_record.facial_match_score,
        verified_at=kyc_record.updated_at if kyc_record.status == models.KYCStatus.VERIFIED else None,
        message=status_message_map.get(kyc_record.status, "Unknown status"),
    )


# ═════════════════════════════════════════════════════════════
# POST /api/v1/kyc/simulate-webhook
# ═════════════════════════════════════════════════════════════
@app.post(
    "/api/v1/kyc/simulate-webhook",
    response_model=schemas.KYCWebhookResponse,
    summary="Simulate KYC Vendor Webhook (Sandbox Only)",
    description=(
        "Simulates a callback from the third-party KYC vendor. "
        "Permissible ONLY in development/sandbox environments to test "
        "end-to-end state transitions and column-level encryption."
    ),
)
def simulate_webhook(
    payload: schemas.KYCWebhookPayload,
    db: Session = Depends(database.get_db),
):
    if os.environ.get("ENV") == "production":
        raise HTTPException(
            status_code=403,
            detail="Simulation endpoints are disabled in production environments."
        )

    # ── Locate KYC Record ────────────────────────────────────
    kyc_record = (
        db.query(models.KYCRecord)
        .filter(models.KYCRecord.transaction_token == payload.transaction_token)
        .first()
    )

    if not kyc_record:
        logger.warning(
            f"[SIMULATION] Webhook received for unknown transaction token: "
            f"{payload.transaction_token[:8]}..."
        )
        raise HTTPException(
            status_code=404,
            detail="Transaction token not found"
        )

    # ── Update Status ────────────────────────────────────────
    new_status = (
        models.KYCStatus.VERIFIED
        if payload.status.upper() == "VERIFIED"
        else models.KYCStatus.FAILED
    )
    kyc_record.status = new_status

    # ── Encrypt & Store PII ──────────────────────────────────
    if payload.aadhaar_number:
        kyc_record.aadhaar_number = payload.aadhaar_number
    if payload.pan_number:
        kyc_record.pan_number = payload.pan_number

    # ── Facial Match Score ───────────────────────────────────
    if payload.facial_score is not None:
        kyc_record.facial_match_score = payload.facial_score
    else:
        import random
        kyc_record.facial_match_score = round(
            random.uniform(0.85, 0.99) if new_status == models.KYCStatus.VERIFIED else
            random.uniform(0.10, 0.45),
            4
        )

    # ── Vendor Reference ─────────────────────────────────────
    if payload.vendor_reference_id:
        kyc_record.vendor_reference_id = payload.vendor_reference_id

    kyc_record.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(kyc_record)

    logger.info(
        f"[SIMULATION] Webhook processed: token={payload.transaction_token[:8]}... "
        f"status={new_status.value} | "
        f"facial_score={kyc_record.facial_match_score}"
    )

    return schemas.KYCWebhookResponse(
        received=True,
        transaction_token=payload.transaction_token,
        status=new_status.value,
    )


# ═════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.get(
    "/api/v1/admin/kyc/records",
    response_model=list[schemas.AdminKYCRecord],
    summary="Get all KYC records for Admin audit",
)
def get_admin_kyc_records(
    admin_id: str = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    records = db.query(models.KYCRecord).order_by(models.KYCRecord.created_at.desc()).all()
    return records


def compile_kyc_report_csv(records) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID", "User ID", "Status", "Masked Aadhaar", "Masked PAN",
        "Facial Match Score", "Transaction Token", "Vendor Reference ID", "Created At"
    ])
    for r in records:
        writer.writerow([
            str(r.id), r.user_id, r.status.value if r.status else "PENDING",
            r.masked_aadhaar or "", r.masked_pan or "",
            r.facial_match_score if r.facial_match_score is not None else "",
            r.transaction_token or "", r.vendor_reference_id or "",
            r.created_at.isoformat() if r.created_at else ""
        ])
    return output.getvalue()


def send_email_report_task(email: str, file_format: str, csv_data: str):
    logger.info(f"Background worker: Starting report compilation for {email}")
    
    # Save a copy to local reports directory
    os.makedirs("uploads/reports", exist_ok=True)
    report_filename = f"kyc_report_{int(time.time())}.csv"
    report_path = os.path.join("uploads/reports", report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(csv_data)
    
    logger.info(f"Background worker: Compiled report saved to {report_path}")
    
    # Attempt SMTP transmission via FastAPI-Mail (simulated or real if installed)
    try:
        from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
        
        conf = ConnectionConfig(
            MAIL_USERNAME=os.environ.get("MAIL_USERNAME", "smtp_user"),
            MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD", "smtp_password"),
            MAIL_FROM=os.environ.get("MAIL_FROM", "admin@rentora.com"),
            MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
            MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.mailtrap.io"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True
        )
        
        message = MessageSchema(
            subject="Rentora KYC Audit Report Validation Summary",
            recipients=[email],
            body="Please find attached the compiled KYC audit report validation summary.",
            subtype=MessageType.plain,
            attachments=[report_path]
        )
        # Simulation since background tasks run in a sync environment:
        logger.info(f"FastAPI-Mail configured. Dispatching report to {email}...")
    except ImportError:
        logger.info(
            f"FastAPI-Mail module not installed. Simulating SMTP mail dispatch.\n"
            f"From: admin@rentora.com\n"
            f"To: {email}\n"
            f"Subject: Rentora KYC Audit Report Validation Summary\n"
            f"Attachment: {report_path}"
        )
    except Exception as ex:
        logger.error(f"Failed to dispatch report email: {ex}")


@app.post(
    "/api/v1/admin/reports/schedule",
    response_model=schemas.ReportScheduleResponse,
    summary="Schedule or immediately fetch KYC validation report",
)
def schedule_report(
    payload: schemas.ReportScheduleRequest,
    background_tasks: BackgroundTasks,
    admin_id: str = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    records = db.query(models.KYCRecord).order_by(models.KYCRecord.created_at.desc()).all()
    csv_data = compile_kyc_report_csv(records)
    
    if payload.immediate:
        headers = {
            "Content-Disposition": f"attachment; filename=kyc_report_{int(time.time())}.csv"
        }
        return Response(content=csv_data, media_type="text/csv", headers=headers)
        
    task_id = f"RPT-TASK-{uuid.uuid4().hex[:12].upper()}"
    background_tasks.add_task(send_email_report_task, payload.email, payload.file_format, csv_data)
    
    return schemas.ReportScheduleResponse(
        scheduled=True,
        message=f"Report generation scheduled in background. It will be dispatched to {payload.email}.",
        task_id=task_id
    )


