from fastapi import FastAPI, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import jwt
import datetime
from typing import List, Optional

from . import models, schemas, database
from .report_generator import generate_pdf_report
from .kafka_consumer import start_metrics_consumer

# ── Config ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("owner_dashboard")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Owner Dashboard Service", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    # Start the background task for Kafka consumption
    import asyncio
    asyncio.create_task(start_metrics_consumer())
    logger.info("Kafka Metrics Consumer started in background.")

# ── Auth ─────────────────────────────────────────────────────────────────────
def get_current_user_info(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"sub": payload.get("sub"), "role": payload.get("role")}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# ── Metrics API ──────────────────────────────────────────────────────────────
@app.get("/owners/{owner_id}/metrics", response_model=schemas.MetricsSummary)
def get_owner_metrics(
    owner_id: str,
    period_start: Optional[datetime.datetime] = None,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    """Fetch high-level business metrics for an owner."""
    if user_info["sub"] != owner_id and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    query = db.query(models.OwnerMetric).filter(models.OwnerMetric.owner_id == owner_id)
    if period_start:
        query = query.filter(models.OwnerMetric.period_start >= period_start)
    
    metrics = query.all()
    
    total_rev = sum(m.revenue_total for m in metrics)
    total_pending = sum(m.pending_rent_total for m in metrics)
    avg_occupancy = (sum(m.occupancy_count for m in metrics) / len(metrics)) * 100 if metrics else 0
    
    return {
        "revenue_total": total_rev,
        "pending_rent_total": total_pending,
        "occupancy_rate": avg_occupancy,
        "history": metrics
    }

# ── Reports API ──────────────────────────────────────────────────────────────
@app.post("/owners/{owner_id}/reports", response_model=schemas.ReportOut)
async def request_report(
    owner_id: str,
    report_type: str, # revenue, occupancy
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    """Trigger PDF report generation."""
    if user_info["sub"] != owner_id and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    metrics = db.query(models.OwnerMetric).filter(models.OwnerMetric.owner_id == owner_id).all()
    
    report_url = generate_pdf_report(owner_id, metrics, report_type)
    
    report = models.OwnerReport(
        owner_id=owner_id,
        report_type=report_type,
        report_path=report_url,
        status="generated"
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report

@app.get("/owners/{owner_id}/reports", response_model=List[schemas.ReportOut])
def list_reports(
    owner_id: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    return db.query(models.OwnerReport).filter(models.OwnerReport.owner_id == owner_id).all()
