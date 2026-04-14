from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, status
from sqlalchemy.orm import Session
import jwt
from typing import List
import time
import asyncio

from . import models, schemas, database
from .storage import S3StubStorage

# Sharing the same secret key as auth service for verification
SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"  
ALGORITHM = "HS256"

# App Setup
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Profile Service")

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

def get_or_create_profile(db: Session, user_identifier: str) -> models.UserProfile:
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_identifier == user_identifier).first()
    if not profile:
        profile = models.UserProfile(user_identifier=user_identifier, kyc_status="not_submitted")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

import logging

@app.get("/", response_model=schemas.ProfileOut)
def get_profile(user_identifier: str = Depends(get_current_user_id), db: Session = Depends(database.get_db)):
    logging.info(f"[ProfileService] Fetching profile data for identifier: {user_identifier}")
    try:
        profile = get_or_create_profile(db, user_identifier)
        
        # Explicit documents fetch
        docs = db.query(models.KYCDocument).filter(models.KYCDocument.profile_id == profile.id).all()
        
        logging.info(f"[ProfileService] Profile found (ID: {profile.id}) for {user_identifier}. Mapping fields...")
        
        # Construct and return profile data with fallback for display
        return {
            "id": profile.id,
            "user_identifier": profile.user_identifier,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "full_name": profile.full_name or f"{profile.first_name or ''} {profile.last_name or ''}".strip() or "New User",
            "email": profile.email or (user_identifier if "@" in user_identifier else None),
            "date_of_birth": profile.date_of_birth,
            "age": profile.age,
            "phone_number": profile.phone_number or (user_identifier if "@" not in user_identifier else None),
            "address": profile.address,
            "permanent_address": profile.permanent_address,
            "city": profile.city,
            "state": profile.state,
            "pincode": profile.pincode,
            "photo_url": profile.photo_url,
            "kyc_status": profile.kyc_status,
            "documents": docs
        }
    except Exception as e:
        logging.error(f"[ProfileService] Critical Error fetching profile for {user_identifier}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Profile data could not be loaded. Please log in again."
        )


@app.put("/", response_model=schemas.ProfileOut)
def update_profile(
    update_data: schemas.ProfileUpdate, 
    user_identifier: str = Depends(get_current_user_id), 
    db: Session = Depends(database.get_db)
):
    try:
        profile = get_or_create_profile(db, user_identifier)
        
        if update_data.first_name is not None:
            profile.first_name = update_data.first_name
        if update_data.last_name is not None:
            profile.last_name = update_data.last_name
        if update_data.email is not None:
            profile.email = update_data.email
        if update_data.full_name is not None:
            profile.full_name = update_data.full_name
        if update_data.date_of_birth is not None:
            profile.date_of_birth = update_data.date_of_birth
        if update_data.age is not None:
            profile.age = update_data.age
        if update_data.phone_number is not None:
            profile.phone_number = update_data.phone_number
        if update_data.address is not None:
            profile.address = update_data.address
        if update_data.permanent_address is not None:
            profile.permanent_address = update_data.permanent_address
        if update_data.city is not None:
            profile.city = update_data.city
        if update_data.state is not None:
            profile.state = update_data.state
        if update_data.pincode is not None:
            profile.pincode = update_data.pincode
        if update_data.photo_url is not None:
            profile.photo_url = update_data.photo_url
            
        db.commit()
        db.refresh(profile)
        
        docs = db.query(models.KYCDocument).filter(models.KYCDocument.profile_id == profile.id).all()
        prof_dict = {
            "id": profile.id,
            "user_identifier": profile.user_identifier,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "full_name": profile.full_name,
            "email": profile.email,
            "date_of_birth": profile.date_of_birth,
            "age": profile.age,
            "phone_number": profile.phone_number,
            "address": profile.address,
            "permanent_address": profile.permanent_address,
            "city": profile.city,
            "state": profile.state,
            "pincode": profile.pincode,
            "photo_url": profile.photo_url,
            "kyc_status": profile.kyc_status,
            "documents": docs
        }
        return prof_dict
    except Exception as e:
        logging.error(f"[ProfileService] Failed to update profile for {user_identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while updating profile")

@app.post("/upload-doc", response_model=schemas.KYCDocumentOut)
def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    user_identifier: str = Depends(get_current_user_id), 
    db: Session = Depends(database.get_db)
):
    profile = get_or_create_profile(db, user_identifier)
    
    # Upload to "S3"
    s3_url = S3StubStorage.upload_file(file.file, file.filename)
    
    # Save record
    new_doc = models.KYCDocument(
        profile_id=profile.id,
        document_type=document_type,
        s3_url=s3_url
    )
    db.add(new_doc)
    
    # Update status to draft if it's the first doc
    if profile.kyc_status == "not_submitted":
        profile.kyc_status = "draft"
    
    db.commit()
    db.refresh(new_doc)
    
    return new_doc

@app.post("/upload-photo")
def upload_photo(
    file: UploadFile = File(...),
    user_identifier: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    profile = get_or_create_profile(db, user_identifier)
    
    # Upload to "S3"
    photo_url = S3StubStorage.upload_file(file.file, file.filename)
    
    # Update profile
    profile.photo_url = photo_url
    db.commit()
    db.refresh(profile)
    
    return {"photo_url": photo_url}

@app.post("/submit-kyc")
async def submit_kyc(
    user_identifier: str = Depends(get_current_user_id), 
    db: Session = Depends(database.get_db)
):
    profile = get_or_create_profile(db, user_identifier)
    
    docs = db.query(models.KYCDocument).filter(models.KYCDocument.profile_id == profile.id).all()
    if not docs:
        raise HTTPException(status_code=400, detail="Must upload at least one KYC document first")
    
    profile.kyc_status = "pending_review"
    db.commit()
    return {"status": "success", "message": "KYC submitted for review"}

@app.post("/verify-kyc")
async def verify_kyc(
    user_identifier: str = Depends(get_current_user_id), 
    db: Session = Depends(database.get_db)
):
    profile = get_or_create_profile(db, user_identifier)
    
    if profile.kyc_status != "pending_review":
        raise HTTPException(status_code=400, detail="KYC must be in pending_review status to be verified")
        
    # Simulate API Call to Digilocker/Aadhaar Authority
    await asyncio.sleep(2)
    
    profile.kyc_status = "verified"
    db.commit()
    return {"status": "success", "message": "KYC Verified successfully"}

# --- MESSAGING ENDPOINTS ---

@app.post("/messages", response_model=schemas.MessageOut)
def send_message(
    message: schemas.MessageCreate,
    user_identifier: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    new_message = models.Message(
        sender_id=user_identifier,
        receiver_id=message.receiver_id,
        property_id=message.property_id,
        body=message.body
    )
    db.add(new_message)
    
    # Auto-create a notification for the receiver
    notification = models.Notification(
        user_id=message.receiver_id,
        type="message",
        content=f"New message regarding property {message.property_id}"
    )
    db.add(notification)
    
    db.commit()
    db.refresh(new_message)
    return new_message

@app.get("/messages/{thread_user_id}", response_model=List[schemas.MessageOut])
def get_thread(
    thread_user_id: str,
    skip: int = 0,
    limit: int = 50,
    user_identifier: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    from sqlalchemy import or_, and_
    messages = db.query(models.Message).filter(
        or_(
            and_(models.Message.sender_id == user_identifier, models.Message.receiver_id == thread_user_id),
            and_(models.Message.sender_id == thread_user_id, models.Message.receiver_id == user_identifier)
        )
    ).order_by(models.Message.created_at.asc()).offset(skip).limit(limit).all()
    
    # Mark as read
    unread_msgs = [m for m in messages if m.receiver_id == user_identifier and not m.is_read]
    for m in unread_msgs:
        m.is_read = True
    if unread_msgs:
        db.commit()
        
    return messages

# --- NOTIFICATION ENDPOINTS ---

@app.get("/notifications", response_model=List[schemas.NotificationOut])
def get_notifications(
    user_identifier: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_identifier
    ).order_by(models.Notification.created_at.desc()).limit(20).all()

@app.patch("/notifications/{notif_id}/read")
def read_notification(
    notif_id: int,
    user_identifier: str = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id,
        models.Notification.user_id == user_identifier
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"status": "success"}
