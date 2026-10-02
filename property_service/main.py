from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session
import jwt
import sys
import os as _os
from typing import List, Optional
from sqlalchemy import func
import logging
import datetime

from . import models, schemas, database
from .media_processor import MediaProcessor
from .location.ola_geocoder import geocode_address

ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from shared_rate_limiter import rate_limit

SECRET_KEY = _os.environ.get("JWT_SECRET_KEY", "RENTORA_SUPER_SECRET_KEY")
ALGORITHM  = "HS256"

_IS_PROD = _os.environ.get("ENV", "").lower() == "production"
_ALLOWED_ORIGINS = (
    ["https://rentora.in", "https://www.rentora.in", "https://app.rentora.in"]
    if _IS_PROD
    else ["http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.1.5:5173"]
)

app = FastAPI(title="Rentora Property Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["X-XSS-Protection"]       = "1; mode=block"
    response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
    if _IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
    if user_info["role"] not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can perform this action")
    return user_info

@app.post("/", response_model=schemas.PropertyOut)
async def create_property(
    prop_data: schemas.PropertyCreate,
    user_info: dict = Depends(require_owner),
    db: Session = Depends(database.get_db)
):
    # ── Resolve coordinates ────────────────────────────────────────────────
    # Priority: caller-supplied lat/lng > Ola Maps geocode > None (stored as null)
    resolved_lat: float | None = prop_data.lat
    resolved_lng: float | None = prop_data.lng

    if resolved_lat is None or resolved_lng is None:
        geo_lat, geo_lng = await geocode_address(
            address=prop_data.address,
            area=prop_data.area or "",
            city=prop_data.city or "Bengaluru",
            pincode=prop_data.pincode or "",
        )
        if geo_lat is not None:
            resolved_lat, resolved_lng = geo_lat, geo_lng
            logging.info(
                f"[PropertyCreate] Geocoded '{prop_data.address}' → "
                f"({resolved_lat:.5f}, {resolved_lng:.5f})"
            )
        else:
            logging.warning(
                f"[PropertyCreate] Geocoding failed for '{prop_data.address}'. "
                "Property will be stored without coordinates."
            )

    new_prop = models.Property(
        owner_id=user_info["sub"],
        title=prop_data.title,
        description=prop_data.description,
        address=prop_data.address,
        area=prop_data.area,
        city=prop_data.city or "Bengaluru",
        state=prop_data.state or "Karnataka",
        country="India",
        property_type=prop_data.property_type,
        price=prop_data.price,
        amenities=prop_data.amenities,
        lat=resolved_lat,
        lng=resolved_lng,
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    
    # Active Cache Invalidation and Event Publishing
    try:
        import shared_redis
        shared_redis.invalidate_search_cache()
        import shared_event_broker
        shared_event_broker.publish_event(
            "property.created",
            {
                "property_id": new_prop.id,
                "title": new_prop.title,
                "description": new_prop.description,
                "address": new_prop.address,
                "property_type": new_prop.property_type,
                "price": new_prop.price,
                "amenities": new_prop.amenities.split(",") if new_prop.amenities else [],
                "status": new_prop.status,
                "lat": new_prop.lat,
                "lng": new_prop.lng
            },
            "property_service"
        )
    except Exception as ex:
        logging.warning(f"Failed to invalidate search cache on property create: {ex}")
        
    return new_prop

@app.put("/properties/{property_id}/status")
def update_property_status(
    property_id: int,
    data: dict,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
):
    """Update property status — requires ownership or admin role."""
    logger = logging.getLogger("property_service")

    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # IDOR guard: only the owner or an admin may change the listing status
    if user_info["role"] != "admin" and prop.owner_id != user_info["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this property.",
        )

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
    
    # Active Cache Invalidation
    try:
        import shared_redis
        shared_redis.delete(shared_redis.get_property_key(property_id))
        shared_redis.invalidate_search_cache()
        import shared_event_broker
        shared_event_broker.publish_event(
            "property.updated" if new_status != "unlisted" else "property.deleted",
            {
                "property_id": prop.id,
                "status": prop.status
            },
            "property_service"
        )
    except Exception as ex:
        logging.warning(f"Failed to invalidate caches on property status update: {ex}")
        
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
    import json
    import shared_redis
    
    # Construct distinct cache key based on query parameters
    q_str = f"q:{q}|min:{min_price}|max:{max_price}|type:{property_type}|amenities:{amenities}|featured:{featured}|verified:{verified}|near:{near_lat},{near_lng}|limit:{limit}"
    cache_key = shared_redis.get_search_key(q_str)
    
    try:
        cached_val = shared_redis.get(cache_key)
        if cached_val:
            return json.loads(cached_val)
    except Exception as ex:
        logging.warning(f"Failed to read search cache: {ex}")
        
    query = db.query(models.Property)
    
    if q:
        query = query.filter(
            models.Property.title.contains(q) | 
            models.Property.address.contains(q) |
            models.Property.area.contains(q) |
            models.Property.city.contains(q) |
            models.Property.state.contains(q)
        )
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
        
    query = query.order_by(models.Property.is_featured.desc(), models.Property.created_at.desc())
    properties = query.all()

    # PostGIS Spatial Filter (replaces legacy haversine calculation)
    if near_lat is not None and near_lng is not None:
        try:
            from sqlalchemy import text as sql_text
            # Use PostGIS ST_DWithin for index-accelerated proximity search
            radius_m = max_dist_km * 1000
            spatial_ids = db.execute(sql_text("""
                SELECT id FROM property.properties
                WHERE geom IS NOT NULL
                  AND ST_DWithin(
                      geom::geography,
                      ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                      :radius
                  )
            """), {"lat": near_lat, "lng": near_lng, "radius": radius_m}).fetchall()
            valid_ids = {r[0] for r in spatial_ids}
            properties = [p for p in properties if p.id in valid_ids]
        except Exception as spatial_err:
            logging.warning(f"PostGIS spatial filter unavailable ({spatial_err}), using haversine fallback")
            filtered = []
            for p in properties:
                if p.lat and p.lng:
                    dist = haversine_distance(near_lat, near_lng, p.lat, p.lng)
                    if dist <= max_dist_km:
                        filtered.append(p)
            properties = filtered

    results = []
    for prop in properties[:limit]:
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
            
        try:
            results.append({
                "id": prop.id,
                "owner_id": prop.owner_id,
                "title": prop.title,
                "description": prop.description,
                "address": prop.address,
                "property_type": prop.property_type,
                "price": prop.price,
                "amenities": prop.amenities or "",
                "commute_score": prop.commute_score,
                "created_at": prop.created_at.isoformat() if prop.created_at else None,
                "media": media_items
            })
        except Exception as e:
            logging.error(f"[PropertyService] Failed to map property {prop.id}: {str(e)}")
            continue
            
    # Save search result to cache for 10 minutes (600s)
    try:
        shared_redis.set(cache_key, json.dumps(results), ttl=600)
    except Exception as ex:
        logging.warning(f"Failed to write search cache: {ex}")
        
    return results





import httpx
import random

@app.get("/search/suggestions")
async def get_suggestions(q: str):
    from .location.maptiler import MaptilerProvider
    provider = MaptilerProvider()
    return await provider.autocomplete(q)

@app.get("/location/pois")
async def get_property_pois(lat: float, lng: float):
    import os
    # Use env var for Docker, fall back to localhost:8014 for local dev
    geo_service_url = os.environ.get("GEO_AMENITY_SERVICE_URL", "http://localhost:8014")
    # Fetch POIs from geo_amenity_service using smart per-category radius
    # (no explicit radius= param → geo service applies 2 km baseline with
    #  5 km for hospitals/offices and auto-expansion fallback for empty results)
    pois = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{geo_service_url}/amenities/nearby?lat={lat}&lng={lng}",
                timeout=25.0
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_amenities = data.get("amenities", [])
                for a in raw_amenities:
                    pois.append({
                        "name": a["name"],
                        # Coordinates from Overpass are already (lat, lng) — pass through unchanged
                        "lat": a["lat"],
                        "lng": a["lng"],
                        "category": a["category"],
                        "distance": a.get("distance_m", 0)
                    })
    except Exception as e:
        import traceback
        print(f"Error fetching POIs from geo_amenity_service (type={type(e)}): {e}")
        traceback.print_exc()
        print("Falling back to provider POIs.")

    # Fallback to maptiler provider if geo_amenity_service returned empty or failed
    if not pois:
        from .location.maptiler import MaptilerProvider
        fallback_provider = MaptilerProvider()
        pois = await fallback_provider.fetch_pois(lat, lng)

    # Select diverse POIs: up to 3 per category, max 30 total
    category_counts: dict = {}
    diverse_pois = []
    for p in pois:
        cat = p.get("category", "other")
        count = category_counts.get(cat, 0)
        if count < 3:
            diverse_pois.append(p)
            category_counts[cat] = count + 1
        if len(diverse_pois) >= 30:
            break
    pois = diverse_pois

    # Routes are fetched on-demand by the frontend via /geo/commute/route
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
    owner_id: Optional[str] = None,
    date_range: Optional[str] = None,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db)
):
    role    = user_info["role"]
    caller  = user_info["sub"]

    # IDOR guard: non-admin callers may only request their own metrics.
    # Silently ignore the owner_id param for non-admins and force it to self.
    if role != "admin" and owner_id and owner_id != caller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to view another user's metrics.",
        )

    user_id = (owner_id if owner_id else caller) if role == "admin" else caller
    logging.info(f"[PropertyService] Calculating metrics for role: {role}, user: {user_id}")
    
    try:
        # Filtering logic
        if role == "admin":
            base_query = db.query(func.count(models.Property.id))
            if owner_id:
                base_query = base_query.filter(models.Property.owner_id == user_id)
            total_listings = base_query.scalar()
            
            total_views = total_listings * 312 
            
            apps_query = db.query(func.count(models.VisitRequest.id))
            if owner_id:
                apps_query = apps_query.filter(models.VisitRequest.owner_id == user_id)
            total_apps = apps_query.scalar()
            
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
    request: Request,
    visit_data: schemas.VisitRequestCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(database.get_db),
    _rl: None = Depends(rate_limit(
        "book_visit", max_calls=10, window_seconds=3600,  # 10/hr per user
        key_fn="user",
        detail="Visit booking limit reached. You may book up to 10 visits per hour.",
    )),
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


@app.get("/{property_id}", response_model=schemas.PropertyDetail)
def get_property_detail(
    property_id: int,
    db: Session = Depends(database.get_db)
):
    import json
    import shared_redis
    
    cache_key = shared_redis.get_property_key(property_id)
    try:
        cached_val = shared_redis.get(cache_key)
        if cached_val:
            return json.loads(cached_val)
    except Exception as ex:
        logging.warning(f"Failed to read property detail cache: {ex}")

    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
        
    # Mock address detail from string
    address_detail = {
        "city": prop.city or "Mumbai",
        "state": prop.state or "Maharashtra",
        "full_address": prop.address,
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

    res_dict = {
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
        "createdAt": prop.created_at.isoformat() if prop.created_at else None,
        "updatedAt": prop.updated_at.isoformat() if prop.updated_at else None
    }
    
    # Save property detail to cache for 1 hour (3600s)
    try:
        shared_redis.set(cache_key, json.dumps(res_dict), ttl=3600)
    except Exception as ex:
        logging.warning(f"Failed to write property detail cache: {ex}")
        
    return res_dict


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
        property_id = event.value.get("property_id")
        if property_id:
            prop = db.query(models.Property).filter(models.Property.id == property_id).first()
            if prop:
                prop.is_featured = True
                db.commit()
                logging.info(f"Property {property_id} is now featured via internal event.")
    return {"status": "ok"}

