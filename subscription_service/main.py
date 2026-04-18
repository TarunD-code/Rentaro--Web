from fastapi import FastAPI, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
import logging
import jwt
import datetime
import json
from typing import List, Optional

from . import models, schemas, database

# ── Config ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("subscription_service")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Subscription Service", version="1.0.0")

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

def require_premium(user_info: dict = Depends(get_current_user_info), db: Session = Depends(database.get_db)):
    sub = db.query(models.Subscription).filter(
        models.Subscription.tenant_id == user_info["sub"],
        models.Subscription.status == "active"
    ).first()
    if not sub:
        raise HTTPException(status_code=403, detail="Premium subscription required for this feature")
    return user_info

# ── Subscription Endpoints ───────────────────────────────────────────────────
@app.get("/status", response_model=Optional[schemas.SubscriptionOut])
def get_subscription_status(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    """Retrieve current subscription status for a tenant."""
    return db.query(models.Subscription).filter(models.Subscription.tenant_id == user_info["sub"]).first()

@app.post("/checkout", response_model=schemas.SubscriptionOut)
async def create_subscription_checkout(
    data: schemas.SubscriptionCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    """Initiate a recurring subscription."""
    # Mocking Razorpay Subscription Creation
    rz_sub_id = f"sub_{datetime.datetime.now().timestamp()}"
    
    new_sub = models.Subscription(
        tenant_id=user_info["sub"],
        plan_key=data.plan_key,
        provider_subscription_id=rz_sub_id,
        status="active", # In demo, activate immediately
        current_period_end=datetime.datetime.utcnow() + datetime.timedelta(days=30)
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    
    # Create initial invoice
    invoice = models.Invoice(
        subscription_id=new_sub.id,
        amount_cents=99900 if data.plan_key == "premium" else 49900,
        status="paid"
    )
    db.add(invoice)
    db.commit()
    
    return new_sub

@app.get("/invoices", response_model=List[schemas.InvoiceOut])
def list_invoices(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    sub = db.query(models.Subscription).filter(models.Subscription.tenant_id == user_info["sub"]).first()
    if not sub:
        return []
    return db.query(models.Invoice).filter(models.Invoice.subscription_id == sub.id).all()

# ── Concierge Endpoints ─────────────────────────────────────────────────────
@app.post("/concierge/requests", response_model=schemas.ConciergeOut)
def create_concierge_request(
    data: schemas.ConciergeCreate,
    user_info: dict = Depends(require_premium),
    db: Session = Depends(database.get_db)
):
    """Submit a concierge task (Viewing, Shortlisting, Booking)."""
    request = models.ConciergeRequest(
        tenant_id=user_info["sub"],
        property_id=data.property_id,
        request_type=data.request_type,
        details=data.details,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

@app.get("/concierge/requests", response_model=List[schemas.ConciergeOut])
def list_concierge_requests(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    return db.query(models.ConciergeRequest).filter(models.ConciergeRequest.tenant_id == user_info["sub"]).all()
