from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import jwt
import os
import datetime

from . import models, database

# Setting up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics_service")

# Ensure tables exist (normally we use Alembic/scripts, but good for local)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Rentora Analytics & Reporting Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_super_secret_jwt_key")
ALGORITHM = "HS256"

def get_current_admin(request: Request):
    """Dependency to extract JWT and verify admin role."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Unauthorised. Admin access required.")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def log_audit(db: Session, admin_id: str, action: str, target: str = None, details: str = None):
    log = models.AuditLog(admin_id=admin_id, action=action, target_entity=target, details=details)
    db.add(log)
    db.commit()


@app.get("/admin/analytics/summary")
def get_analytics_summary(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """
    Returns aggregated figures for the dashboard overview.
    Queries the latest DailyAggregateSnapshot.
    """
    latest = db.query(models.DailyAggregateSnapshot).order_by(models.DailyAggregateSnapshot.report_date.desc()).first()
    
    if not latest:
        # Fallback empty metrics if no snapshot has run
        return {
            "total_revenue": 0.0,
            "pending_payouts": 0.0,
            "occupancy_rate_30d": 0.0,
            "active_mandates": 0,
            "failed_refunds": 0.0
        }
        
    return {
        "total_revenue": latest.total_revenue,
        "pending_payouts": latest.pending_payouts_volume,
        "occupancy_rate_30d": latest.occupancy_rate / 100.0, # return as decimal e.g. 0.92
        "active_mandates": latest.total_active_mandates,
        "failed_refunds": latest.failed_refunds_volume
    }


@app.get("/admin/analytics/ledger")
def get_ledger_aggregates(
    period: str = "30d",
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Admin endpoint to see platform ledger aggregation."""
    # In a full cross-db setup this aggregates the `rentora_payments.db` ledger entries.
    # For Sprint 15 demo logic we will mock this or return static if not fully simulated in ETl
    return {
        "period": period,
        "fees_collected": 15000,
        "taxes_collected": 2700,
        "owner_payouts": 250000,
        "refunds": 5000
    }


@app.get("/admin/analytics/maintenance")
def get_maintenance_analytics(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """SLA metrics: avg time to resolve, open vs overdue"""
    latest = db.query(models.DailyAggregateSnapshot).order_by(models.DailyAggregateSnapshot.report_date.desc()).first()
    if not latest:
        return {"avg_resolution_hours": 0, "open": 0, "overdue": 0}

    return {
        "avg_resolution_hours": latest.avg_resolution_time_hours,
        "open": latest.total_open_maintenance,
        "overdue": latest.total_overdue_maintenance
    }


@app.get("/admin/analytics/payouts/reconciliation")
def get_reconciliation_mismatches(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Return reconciliation mismatches and suggested actions."""
    # Mock return for admin reconciliation queue
    return {
        "mismatches": [
            {"payout_id": 999, "status_local": "processed", "status_bank": "failed", "suggested_action": "Reverse ledger entry"}
        ],
        "total_unreconciled": 1
    }


@app.get("/admin/analytics/export")
def generate_report(
    type: str = "pdf",
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Exports CSV or PDF of the monthly aggregate."""
    log_audit(db, admin["sub"], f"download_report_{type}")
    
    # Normally returns raw byte data or signed URL. Mocking for demonstration.
    return {"message": f"Successfully generated {type.upper()} report."}
