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

@app.get("/", response_model=schemas.ProfileOut)
def get_profile(user_identifier: str = Depends(get_current_user_id), db: Session = Depends(database.get_db)):
    profile = get_or_create_profile(db, user_identifier)
    
    # Manually attach documents for the response
    docs = db.query(models.KYCDocument).filter(models.KYCDocument.profile_id == profile.id).all()
    # Build response dict
    prof_dict = {
        "id": profile.id,
        "user_identifier": profile.user_identifier,
        "full_name": profile.full_name,
        "date_of_birth": profile.date_of_birth,
        "address": profile.address,
        "kyc_status": profile.kyc_status,
        "documents": docs
    }
    return prof_dict

@app.put("/", response_model=schemas.ProfileOut)
def update_profile(
    update_data: schemas.ProfileUpdate, 
    user_identifier: str = Depends(get_current_user_id), 
    db: Session = Depends(database.get_db)
):
    profile = get_or_create_profile(db, user_identifier)
    
    if update_data.full_name is not None:
        profile.full_name = update_data.full_name
    if update_data.date_of_birth is not None:
        profile.date_of_birth = update_data.date_of_birth
    if update_data.address is not None:
        profile.address = update_data.address
        
    db.commit()
    db.refresh(profile)
    
    docs = db.query(models.KYCDocument).filter(models.KYCDocument.profile_id == profile.id).all()
    prof_dict = {
        "id": profile.id,
        "user_identifier": profile.user_identifier,
        "full_name": profile.full_name,
        "date_of_birth": profile.date_of_birth,
        "address": profile.address,
        "kyc_status": profile.kyc_status,
        "documents": docs
    }
    return prof_dict

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
