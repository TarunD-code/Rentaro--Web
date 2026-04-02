from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, status
from sqlalchemy.orm import Session
import jwt
from typing import List, Optional

from . import models, schemas, database
from .media_processor import MediaProcessor

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"  
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Property Service")

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

def require_owner(user_info: dict = Depends(get_current_user_info)):
    if user_info["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can perform this action")
    return user_info

@app.post("/", response_model=schemas.PropertyOut)
def create_property(
    prop_data: schemas.PropertyCreate,
    user_info: dict = Depends(require_owner),
    db: Session = Depends(database.get_db)
):
    new_prop = models.Property(
        owner_id=user_info["sub"],
        title=prop_data.title,
        description=prop_data.description,
        address=prop_data.address,
        price=prop_data.price,
        amenities=prop_data.amenities
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@app.get("/", response_model=List[schemas.PropertyOut])
def list_properties(
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    limit: Optional[int] = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Property)
    
    if q:
        query = query.filter(models.Property.title.contains(q) | models.Property.address.contains(q))
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)
    if featured is not None:
        query = query.filter(models.Property.is_featured == featured)
        
    properties = query.limit(limit).all()
    return properties

@app.get("/{property_id}", response_model=schemas.PropertyDetail)
def get_property_detail(
    property_id: int,
    db: Session = Depends(database.get_db)
):
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
        
    # Mock address detail from string
    address_detail = {
        "city": prop.city or "Mumbai",
        "state": prop.state or "Maharashtra",
        "country": prop.country or "India",
        "geo": {"lat": prop.lat or 19.0760, "lng": prop.lng or 72.8777}
    }
    
    # Mock host info (In production, fetch from profile_service)
    host_info = {
        "id": prop.owner_id,
        "name": "Trusted Host",
        "verified": True,
        "responseTime": "Within 1h"
    }

    # Format media to match MediaItem schema
    media_items = []
    for m in prop.media:
        media_items.append({
            "id": m.id,
            "type": m.file_type or "image",
            "url": m.raw_url,
            "thumbnailUrl": m.thumb_url,
            "mime": m.mime_type,
            "size": m.size
        })

    return {
        "id": prop.id,
        "title": prop.title,
        "description": prop.description,
        "price": prop.price,
        "currency": prop.currency or "INR",
        "address": address_detail,
        "amenities": prop.amenities.split(",") if prop.amenities else [],
        "media": media_items,
        "host": host_info,
        "createdAt": prop.created_at,
        "updatedAt": prop.updated_at
    }

@app.get("/search/suggestions")
def get_suggestions(q: str):
    # Seeded list of major Indian cities for MVP
    cities = [
        "Mumbai", "Delhi", "Bengaluru", "Bangalore", "Hyderabad", "Ahmedabad", 
        "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow", "Kanpur"
    ]
    if not q:
        return []
    
    q_lower = q.lower()
    matches = [c for c in cities if q_lower in c.lower()]
    return matches[:5]

@app.post("/{property_id}/upload-media", response_model=schemas.PropertyMediaOut)
def upload_media(
    property_id: int,
    file: UploadFile = File(...),
    user_info: dict = Depends(require_owner),
    db: Session = Depends(database.get_db)
):
    # Verify ownership
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.owner_id != user_info["sub"]:
        raise HTTPException(status_code=403, detail="You do not own this property")

    # Process and store
    media_meta = MediaProcessor.process_and_store(file.file, file.filename)
    
    new_media = models.PropertyMedia(
        property_id=property_id,
        file_type="image" if "image" in media_meta["mime"] else "video",
        raw_url=media_meta["url"],
        thumb_url=media_meta["thumbnailUrl"],
        mime_type=media_meta["mime"],
        size=media_meta["size"],
        width=media_meta["width"],
        height=media_meta["height"]
    )
    db.add(new_media)
    db.commit()
    db.refresh(new_media)
    
    return new_media

@app.post("/favorites/{property_id}")
def add_favorite(
    property_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    # Check if exists
    existing = db.query(models.Favorite).filter(
        models.Favorite.user_id == user_info["sub"],
        models.Favorite.property_id == property_id
    ).first()
    
    if not existing:
        fav = models.Favorite(user_id=user_info["sub"], property_id=property_id)
        db.add(fav)
        db.commit()
    
    return {"status": "success"}

@app.delete("/favorites/{property_id}")
def remove_favorite(
    property_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    db.query(models.Favorite).filter(
        models.Favorite.user_id == user_info["sub"],
        models.Favorite.property_id == property_id
    ).delete()
    db.commit()
    return {"status": "success"}

@app.get("/favorites")
def get_favorites(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    favorites = db.query(models.Favorite).filter(models.Favorite.user_id == user_info["sub"]).all()
    # Return as list of property IDs for easier frontend consumption
    return [f.property_id for f in favorites]
