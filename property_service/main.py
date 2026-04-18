from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, status
from sqlalchemy.orm import Session
import jwt
from typing import List, Optional
from sqlalchemy import func

from . import models, schemas, database
from .media_processor import MediaProcessor
from .location import provider as loc_provider

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
        property_type=prop_data.property_type,
        price=prop_data.price,
        amenities=prop_data.amenities
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@app.put("/properties/{property_id}/status")
def update_property_status(
    property_id: int,
    data: dict,
    db: Session = Depends(database.get_db),
):
    """Update property status (used by payment service for auto-relisting)."""
    import logging
    logger = logging.getLogger("property_service")

    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    new_status = data.get("status", "available")
    valid_statuses = ["available", "occupied", "maintenance", "unlisted"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    prop.status = new_status
    if new_status == "available":
        import datetime
        prop.available_from = data.get("available_from") or datetime.datetime.utcnow()

    db.commit()
    db.refresh(prop)
    logger.info(f"Property #{property_id} status updated to '{new_status}'")
    return {"id": prop.id, "status": prop.status, "available_from": str(prop.available_from)}

import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth."""
    R = 6371 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.get("/", response_model=List[schemas.PropertyOut])
def list_properties(
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    property_type: Optional[str] = None,
    amenities: Optional[str] = None,
    featured: Optional[bool] = None,
    verified: Optional[bool] = None,
    owner_verified: Optional[bool] = None,
    furnished: Optional[bool] = None,
    pet_friendly: Optional[bool] = None,
    near_lat: Optional[float] = None,
    near_lng: Optional[float] = None,
    max_dist_km: Optional[float] = 5.0,
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
    if property_type:
        query = query.filter(models.Property.property_type == property_type)
    if amenities:
        for amt in amenities.split(","):
            query = query.filter(models.Property.amenities.contains(amt.strip()))
    if featured is not None:
        query = query.filter(models.Property.is_featured == featured)
    if verified is not None:
        query = query.filter(models.Property.is_verified == verified)
    if owner_verified is not None:
        query = query.filter(models.Property.owner_verified == owner_verified)
    if furnished is not None:
        query = query.filter(models.Property.is_furnished == furnished)
    if pet_friendly is not None:
        query = query.filter(models.Property.is_pet_friendly == pet_friendly)
        
    properties = query.all()

    # Manual Distance Filter (Haversine) - Since SQLite lacks native spatial indices
    if near_lat is not None and near_lng is not None:
        filtered = []
        for p in properties:
            if p.lat and p.lng:
                dist = haversine_distance(near_lat, near_lng, p.lat, p.lng)
                if dist <= max_dist_km:
                    filtered.append(p)
        properties = filtered

    results = []
    for prop in properties[:limit]:
    
    # Manually map to handle MediaItem field mismatches (url vs raw_url, etc.)
    results = []
    for prop in properties:
        # Create media items list
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
            
        # Manually map to handle MediaItem field mismatches (url vs raw_url, etc.)
        try:
            results.append({
                "id": prop.id,
                "owner_id": prop.owner_id,
                "title": prop.title,
                "description": prop.description,
                "address": prop.address,
                "property_type": prop.property_type,
                "price": prop.price,
                "amenities": prop.amenities,
                "commute_score": prop.commute_score,
                "created_at": prop.created_at,
                "media": media_items
            })
        except Exception as e:
            logging.error(f"[PropertyService] Failed to map property {prop.id}: {str(e)}")
            continue
        
    return results

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

    # Get Reviews aggregation
    avg_rating = db.query(func.avg(models.Review.rating)).filter(models.Review.property_id == property_id).scalar() or 0.0
    reviews_count = db.query(func.count(models.Review.id)).filter(models.Review.property_id == property_id).scalar() or 0

    return {
        "id": prop.id,
        "title": prop.title,
        "description": prop.description,
        "price": prop.price,
        "currency": prop.currency or "INR",
        "property_type": prop.property_type or "Apartment",
        "address": address_detail,
        "amenities": prop.amenities.split(",") if prop.amenities else [],
        "average_rating": float(avg_rating),
        "reviews_count": reviews_count,
        "media": media_items,
        "host": host_info,
        "createdAt": prop.created_at,
        "updatedAt": prop.updated_at
    }

import httpx
import random

@app.get("/search/suggestions")
async def get_suggestions(q: str):
    return await loc_provider.autocomplete(q)

@app.get("/location/pois")
async def get_property_pois(lat: float, lng: float):
    # Fetch POIs securely through provider
    pois = await loc_provider.fetch_pois(lat, lng)
    
    # Pre-calculate simple routing for each POI
    for p in pois:
        route = await loc_provider.get_route((lat, lng), (p["lat"], p["lng"]))
        p["route"] = route
        
    return {"pois": pois}


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

# --- REVIEWS ENDPOINTS ---

@app.post("/{property_id}/reviews", response_model=schemas.ReviewOut)
def create_review(
    property_id: int,
    review_data: schemas.ReviewCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    new_review = models.Review(
        property_id=property_id,
        reviewer_id=user_info["sub"],
        rating=review_data.rating,
        text=review_data.text
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    # Invalidate analytics cache
    if user_info["sub"] in _analytics_cache:
        del _analytics_cache[user_info["sub"]]
        
    return new_review

@app.get("/{property_id}/reviews", response_model=List[schemas.ReviewOut])
def get_property_reviews(
    property_id: int,
    db: Session = Depends(database.get_db)
):
    return db.query(models.Review).filter(
        models.Review.property_id == property_id
    ).order_by(models.Review.created_at.desc()).all()


# --- ANALYTICS ENDPOINTS ---

_analytics_cache = {} # Simple LRU mapping fallback

@app.get("/analytics/host", response_model=schemas.HostAnalyticsOut)
def get_host_analytics(
    user_info: dict = Depends(require_owner),
    db: Session = Depends(database.get_db)
):
    host_id = user_info["sub"]
    
    if host_id in _analytics_cache:
        return _analytics_cache[host_id]
        
    properties = db.query(models.Property).filter(models.Property.owner_id == host_id).all()
    if not properties:
        res = {"total_views": 0, "total_inquiries": 0, "total_favorites": 0, "average_rating": 0.0}
        return res
        
    property_ids = [p.id for p in properties]
    
    total_views = len(property_ids) * 142 # Mock scaler
    total_inquiries = len(property_ids) * 5 # Mock scaler
    
    total_favorites = db.query(func.count(models.Favorite.id)).filter(models.Favorite.property_id.in_(property_ids)).scalar() or 0
    avg_rating = db.query(func.avg(models.Review.rating)).filter(models.Review.property_id.in_(property_ids)).scalar() or 0.0
    
    res = {
        "total_views": total_views,
        "total_inquiries": total_inquiries,
        "total_favorites": total_favorites,
        "average_rating": float(avg_rating)
    }
    
    _analytics_cache[host_id] = res
    return res

@app.get("/metrics", response_model=schemas.DashboardMetricsOut)
def get_dashboard_metrics(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    role = user_info["role"]
    user_id = user_info["sub"]
    logging.info(f"[PropertyService] Calculating metrics for role: {role}, user: {user_id}")
    
    try:
        if role == "admin":
            total_listings = db.query(func.count(models.Property.id)).scalar()
            total_views = total_listings * 312 # Weighted mock scale
            total_apps = db.query(func.count(models.VisitRequest.id)).scalar()
            pending_rent = 1450000.0 # Aggregate mock
        elif role == "owner":
            properties = db.query(models.Property).filter(models.Property.owner_id == user_id).all()
            prop_ids = [p.id for p in properties]
            total_listings = len(prop_ids)
            total_views = total_listings * 195
            total_apps = db.query(func.count(models.VisitRequest.id)).filter(models.VisitRequest.property_id.in_(prop_ids)).scalar() if prop_ids else 0
            pending_rent = 65000.0 if total_listings > 0 else 0.0
        else: # tenant
            total_listings = 0
            total_views = db.query(func.count(models.Favorite.id)).filter(models.Favorite.user_id == user_id).scalar()
            total_apps = db.query(func.count(models.VisitRequest.id)).filter(models.VisitRequest.tenant_id == user_id).scalar()
            pending_rent = 18500.0 if total_apps > 0 else 0.0
            
        logging.info(f"[PropertyService] Metrics calculated successfully for {user_id}")
        return {
            "total_active_listings": int(total_listings or 0),
            "total_views": int(total_views or 0),
            "total_applications": int(total_apps or 0),
            "pending_rent": float(pending_rent or 0.0),
            "role": str(role or "tenant")
        }
    except Exception as e:
        logging.error(f"[PropertyService] Failed to calculate metrics for {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Dashboard metrics unavailable. Please refresh."
        )


# --- VISIT BOOKING ENDPOINTS ---

@app.post("/visits", response_model=schemas.VisitRequestOut)
def request_visit(
    visit_data: schemas.VisitRequestCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    # Verify property exists
    prop = db.query(models.Property).filter(models.Property.id == visit_data.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
        
    new_visit = models.VisitRequest(
        property_id=visit_data.property_id,
        tenant_id=user_info["sub"],
        owner_id=prop.owner_id,
        requested_slot=visit_data.requested_slot
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    return new_visit

@app.get("/visits/host", response_model=List[schemas.VisitRequestOut])
def get_host_visits(
    user_info: dict = Depends(require_owner),
    db: Session = Depends(database.get_db)
):
    return db.query(models.VisitRequest).filter(models.VisitRequest.owner_id == user_info["sub"]).all()

@app.patch("/visits/{visit_id}", response_model=schemas.VisitRequestOut)
def update_visit_status(
    visit_id: int,
    update_data: schemas.VisitRequestUpdate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    visit = db.query(models.VisitRequest).filter(models.VisitRequest.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit request not found")
        
    # Only owner or tenant (for cancellation) can update
    if user_info["sub"] != visit.owner_id and user_info["sub"] != visit.tenant_id:
         raise HTTPException(status_code=403, detail="Not authorized to update this visit")
         
    if update_data.status:
        visit.status = update_data.status
    if update_data.owner_response:
        visit.owner_response = update_data.owner_response
        
    db.commit()
    db.refresh(visit)
    return visit

# --- DIGITAL AGREEMENT ENDPOINTS ---

from .services import PDFGenerator, SignNowProvider, DocumentVault
from fastapi.responses import Response

pdf_gen = PDFGenerator()
esign_provider = SignNowProvider(token="mock_token")
doc_vault = DocumentVault()

@app.post("/agreements/generate", response_model=schemas.RentalAgreementOut)
def generate_agreement(
    agreement_data: schemas.RentalAgreementCreate,
    user_info: dict = Depends(get_current_user_info), # Anyone can initiate draft for demo? Actually, only owner.
    db: Session = Depends(database.get_db)
):
    # Verify property and ownership
    prop = db.query(models.Property).filter(models.Property.id == agreement_data.property_id).first()
    if not prop or prop.owner_id != user_info["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate agreement for this property")
        
    # Create Record
    new_agreement = models.RentalAgreement(
        property_id=agreement_data.property_id,
        tenant_id=agreement_data.tenant_id,
        owner_id=user_info["sub"],
        status="draft",
        metadata_json=agreement_data.metadata_json
    )
    db.add(new_agreement)
    db.commit()
    db.refresh(new_agreement)
    
    # Generate PDF Context
    context = {
        "property_id": prop.id,
        "property_title": prop.title,
        "property_address": f"{prop.address.street}, {prop.address.city}",
        "currency": prop.currency,
        "price": prop.price,
        "tenant_id": new_agreement.tenant_id,
        "owner_id": new_agreement.owner_id,
        "created_at": datetime.datetime.utcnow().strftime("%B %d, %Y"),
        "signature_hash_placeholder": "[PENDING SIGNATURES]",
        "agreement_id": new_agreement.id
    }
    
    # Produce PDF payload
    pdf_bytes = pdf_gen.generate_agreement_pdf(context)
    
    # Store to Vault and register checksum
    doc_hash = doc_vault.store_document(new_agreement.id, pdf_bytes)
    new_agreement.document_hash = doc_hash
    db.commit()
    db.refresh(new_agreement)
    
    return new_agreement

@app.get("/agreements/{agreement_id}", response_model=schemas.RentalAgreementOut)
def get_agreement(
    agreement_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    agreement = db.query(models.RentalAgreement).filter(models.RentalAgreement.id == agreement_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
        
    if user_info["sub"] not in [agreement.tenant_id, agreement.owner_id] and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this agreement")
        
    return agreement

@app.post("/agreements/{agreement_id}/sign", response_model=schemas.RentalAgreementOut)
async def sign_agreement(
    agreement_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    agreement = db.query(models.RentalAgreement).filter(models.RentalAgreement.id == agreement_id).first()
    if not agreement:
         raise HTTPException(status_code=404, detail="Agreement not found")
         
    role = "owner" if user_info["sub"] == agreement.owner_id else "tenant"
    
    # Get signing session
    esign_resp = await esign_provider.request_signature(agreement.id, role, f"{user_info['sub']}@rentora.test")
    
    # Verify signing execution
    verify_resp = esign_provider.verify_signature(esign_resp["session_id"])
    
    if verify_resp["is_valid"]:
        doc_vault.sign_document_event(agreement.id, role, user_info["sub"], verify_resp["signature_hash"])
        
        # State Transition
        if agreement.status == "draft":
            agreement.status = "pending_signatures"
        elif agreement.status == "pending_signatures":
            agreement.status = "signed"
            agreement.signed_at = datetime.datetime.utcnow()
            
        agreement.signnow_id = esign_resp["session_id"]
        db.commit()
        db.refresh(agreement)
        
    return agreement

@app.get("/agreements/{agreement_id}/download")
def download_signed_pdf(
    agreement_id: int,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    agreement = db.query(models.RentalAgreement).filter(models.RentalAgreement.id == agreement_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
        
    if user_info["sub"] not in [agreement.tenant_id, agreement.owner_id] and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        pdf_bytes = doc_vault.retrieve_document(agreement_id)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        raise HTTPException(status_code=404, detail="Agreement PDF not generated or archived")

@app.get("/agreements/user/list", response_model=List[schemas.RentalAgreementOut])
def list_user_agreements(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    if user_info["role"] == "admin":
        return db.query(models.RentalAgreement).all()
    return db.query(models.RentalAgreement).filter(
        (models.RentalAgreement.tenant_id == user_info["sub"]) | 
        (models.RentalAgreement.owner_id == user_info["sub"])
    ).all()


