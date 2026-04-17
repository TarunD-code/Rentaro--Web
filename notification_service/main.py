import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt
import asyncio

from . import models, schemas, database

# Config
SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

# Initialize DB
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Rentora Notification Service", version="1.0.0")

# --- Auth Helper ---
def get_current_user_id(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_identifier
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- Preferences Helper ---
def get_or_create_preferences(db: Session, user_id: str) -> models.NotificationPreference:
    prefs = db.query(models.NotificationPreference).filter(
        models.NotificationPreference.user_id == user_id
    ).first()
    if not prefs:
        prefs = models.NotificationPreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

# --- Endpoints ---

@app.get("/", response_model=List[schemas.NotificationOut])
def get_notifications(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    """Fetch user notifications."""
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id
    ).order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()

@app.patch("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(
    notification_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    """Mark a notification as read."""
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == user_id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

@app.get("/preferences", response_model=schemas.PreferenceOut)
def get_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    """Fetch notification preferences."""
    return get_or_create_preferences(db, user_id)

@app.put("/preferences", response_model=schemas.PreferenceOut)
def update_preferences(
    data: schemas.PreferenceUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    """Update notification preferences."""
    prefs = get_or_create_preferences(db, user_id)
    prefs.push_enabled = data.push_enabled
    prefs.email_enabled = data.email_enabled
    prefs.sms_enabled = data.sms_enabled
    db.commit()
    db.refresh(prefs)
    return prefs

# --- Kafka Consumer Integration (Async Task) ---
@app.on_event("startup")
async def startup_event():
    logger.info("Notification service starting up...")
    # NOTE: In a real environment, we'd start the Kafka consumer as a background task
    # asyncio.create_task(run_kafka_consumer())
    pass
