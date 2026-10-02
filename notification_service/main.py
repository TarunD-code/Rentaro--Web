import logging
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import jwt
from datetime import datetime
from typing import List

from . import models, schemas, database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

# JWT Config (Matches other services)
SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

app = FastAPI(title="Rentora Notification Service")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user_info(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or missing authorization header"
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"sub": user_identifier, "role": payload.get("role")}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.get("/health", response_model=schemas.HealthOut)
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/register", response_model=schemas.TokenOut)
def register_device_token(
    token_data: schemas.TokenRegister,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    user_id = user_info["sub"]
    logger.info(f"Registering device token for user {user_id} on {token_data.platform}")

    # Check if token already exists for this user
    existing_token = db.query(models.NotificationToken).filter(
        models.NotificationToken.device_token == token_data.device_token
    ).first()

    if existing_token:
        existing_token.user_id = user_id
        existing_token.platform = token_data.platform
        existing_token.is_active = True
        existing_token.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_token)
        return existing_token

    # Create new token registration
    new_token = models.NotificationToken(
        user_id=user_id,
        device_token=token_data.device_token,
        platform=token_data.platform
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token

@app.get("/", response_model=List[schemas.NotificationOut])
@app.get("/history", response_model=List[schemas.NotificationOut])
def get_notification_history(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    return db.query(models.NotificationHistory).filter(
        models.NotificationHistory.user_id == user_info["sub"]
    ).order_by(models.NotificationHistory.created_at.desc()).all()

@app.patch("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_as_read(
    notification_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    notif = db.query(models.NotificationHistory).filter(
        models.NotificationHistory.id == notification_id,
        models.NotificationHistory.user_id == user_info["sub"]
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

# Placeholder for real FCMSend
def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
    # This would involve firebase-admin in production
    logger.info(f"[MOCK] Sending push to {user_id}: {title} - {body}")
    # In a real implementation, you'd fetch tokens from NotificationToken filtered by user_id
    return True

from pydantic import BaseModel

class InternalEvent(BaseModel):
    topic: str
    value: dict

@app.post("/internal/events")
def handle_internal_event(
    event: InternalEvent,
    db: Session = Depends(database.get_db)
):
    if event.topic == "featured-listing-purchases":
        owner_id = event.value.get("owner_id")
        amount = event.value.get("amount")
        if owner_id:
            title = "Property Featured!"
            message = f"Your property is now featured. Payment of ₹{amount} was successful."
            notif = models.NotificationHistory(
                user_id=owner_id,
                title=title,
                message=message,
                type="promotion"
            )
            db.add(notif)
            db.commit()
            send_push_notification(owner_id, title, message)
    return {"status": "ok"}

