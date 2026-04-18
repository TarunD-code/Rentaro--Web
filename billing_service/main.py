from fastapi import FastAPI, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
import logging
import jwt
import datetime
import json
from typing import List, Optional

from . import models, schemas, database
from .kafka_producer import KafkaProducer

# ── Config ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("billing_service")

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Billing Service", version="1.0.0")

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

# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/products", response_model=List[schemas.ProductOut])
def list_featured_products(db: Session = Depends(database.get_db)):
    """List available featured listing tiers."""
    products = db.query(models.FeaturedProduct).all()
    if not products:
        # Seed default products if empty
        bronze = models.FeaturedProduct(name="Bronze", duration_days=7, price_inr=199, priority=1)
        silver = models.FeaturedProduct(name="Silver", duration_days=15, price_inr=499, priority=2)
        gold = models.FeaturedProduct(name="Gold", duration_days=30, price_inr=999, priority=3)
        db.add_all([bronze, silver, gold])
        db.commit()
        products = [bronze, silver, gold]
    return products

@app.post("/checkout", response_model=schemas.PurchaseOut)
async def create_checkout_session(
    data: schemas.CheckoutRequest,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    """Initiate featured listing purchase via Razorpay."""
    product = db.query(models.FeaturedProduct).filter(models.FeaturedProduct.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Mock Razorpay Order Creation (Simulating real integration)
    rz_order_id = f"order_feat_{datetime.datetime.now().timestamp()}"
    
    purchase = models.FeaturedPurchase(
        owner_id=user_info["sub"],
        property_id=data.property_id,
        product_id=data.product_id,
        amount=product.price_inr,
        razorpay_order_id=rz_order_id,
        transaction_status="pending"
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    return purchase

@app.post("/webhook/razorpay")
async def razorpay_webhook_featured(request: Request, db: Session = Depends(database.get_db)):
    """Handle Razorpay webhook for featured listing payments."""
    # (Simplified signature verification and processing for MVP)
    body = await request.body()
    payload = json.loads(body)
    event = payload.get("event")
    
    if event == "payment.captured":
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        
        purchase = db.query(models.FeaturedPurchase).filter(models.FeaturedPurchase.razorpay_order_id == order_id).first()
        if purchase and purchase.transaction_status != "completed":
            purchase.transaction_status = "completed"
            purchase.razorpay_payment_id = payment.get("id")
            purchase.start_at = datetime.datetime.utcnow()
            purchase.end_at = purchase.start_at + datetime.timedelta(days=purchase.product.duration_days)
            db.commit()

            # Emit Kafka Event
            event_data = {
                "event_id": f"evt_{datetime.datetime.now().timestamp()}",
                "event_type": "featured.purchase.completed",
                "occurred_at": datetime.datetime.utcnow().isoformat(),
                "payload": {
                    "purchase_id": purchase.id,
                    "owner_id": purchase.owner_id,
                    "property_id": purchase.property_id,
                    "amount": purchase.amount,
                    "priority": purchase.product.priority
                }
            }
            await KafkaProducer.produce("featured-listing-purchases", event_data)
            logger.info(f"Featured entitlement granted for property {purchase.property_id}")

    return {"status": "ok"}
