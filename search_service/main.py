import time
import json
import logging
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, Query, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import get_db, engine, Base
from .schemas import SearchQuery, SearchResponse, AutocompleteResponse, TrackEventRequest
from .ranking_engine import rank_properties
from .autocomplete import get_autocomplete_suggestions, track_search_query, get_trending_searches, get_contextual_suggestions
from .analytics import track_property_view, track_search, track_event
from .recommendations import get_similar_properties, get_recommendations_for_user, get_trending_in_locality, get_commute_recommendations, get_people_also_viewed
from .embeddings import semantic_search

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("search_service")

app = FastAPI(title="Rentora Search Intelligence Platform", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user_id(request: Request) -> Optional[str]:
    # Placeholder for auth logic
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub") or payload.get("user_id")
        except Exception:
            pass
    return None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "search_service"}

@app.post("/search/properties", response_model=SearchResponse)
def search_properties(
    query: SearchQuery,
    request: Request,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    user_id = get_current_user_id(request)
    
    # Track the search event async
    track_search(
        query=query.q or "",
        filters=query.model_dump(exclude={"q"}),
        result_count=0, # Will update via analytics worker later, or just fire and forget
        user_id=user_id
    )
    if query.q:
        track_search_query(query.q)

    # 1. Semantic Search attempt if active
    # (If no query, skip semantic)
    # For now, let's just do FTS, but if 'semantic' flag is passed, we could branch.
    
    # Build FTS + PostGIS query
    sql_params = {}
    where_clauses = ["status = 'available'"]
    
    if query.q:
        # FTS and Trigram
        q_clean = query.q.strip()
        sql_params["q"] = q_clean
        sql_params["q_fts"] = " | ".join(q_clean.split())
        where_clauses.append("""
            (
                search_vector @@ to_tsquery('english', :q_fts) 
                OR similarity(title, :q) > 0.2
                OR similarity(address, :q) > 0.2
                OR area ILIKE '%' || :q || '%'
                OR city ILIKE '%' || :q || '%'
                OR state ILIKE '%' || :q || '%'
            )
        """)
        
    if query.min_price is not None:
        where_clauses.append("price >= :min_price")
        sql_params["min_price"] = query.min_price
    if query.max_price is not None:
        where_clauses.append("price <= :max_price")
        sql_params["max_price"] = query.max_price
    if query.property_type:
        where_clauses.append("property_type = :property_type")
        sql_params["property_type"] = query.property_type
    if query.furnished is not None:
        where_clauses.append("is_furnished = :furnished")
        sql_params["furnished"] = query.furnished
    if query.pet_friendly is not None:
        where_clauses.append("is_pet_friendly = :pet_friendly")
        sql_params["pet_friendly"] = query.pet_friendly
    if query.locality_score_min is not None:
        where_clauses.append("locality_score >= :locality_score_min")
        sql_params["locality_score_min"] = query.locality_score_min
    if query.commute_score_min is not None:
        where_clauses.append("commute_score >= :commute_score_min")
        sql_params["commute_score_min"] = query.commute_score_min
        
    # Geo search
    if query.near_lat is not None and query.near_lng is not None:
        where_clauses.append("""
            ST_DWithin(
                ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography, 
                ST_SetSRID(ST_MakePoint(:near_lng, :near_lat), 4326)::geography, 
                :radius_meters
            )
        """)
        sql_params["near_lat"] = query.near_lat
        sql_params["near_lng"] = query.near_lng
        sql_params["radius_meters"] = query.radius_km * 1000

    if query.min_lat is not None and query.max_lat is not None and query.min_lng is not None and query.max_lng is not None:
        where_clauses.append("lat BETWEEN :min_lat AND :max_lat AND lng BETWEEN :min_lng AND :max_lng")
        sql_params["min_lat"] = query.min_lat
        sql_params["max_lat"] = query.max_lat
        sql_params["min_lng"] = query.min_lng
        sql_params["max_lng"] = query.max_lng

    # Select fields for ranking
    select_fields = """
        property_id, title, description, address, city, state,
        property_type, price, lat, lng, amenities, is_featured, is_verified, 
        owner_verified, media_count, view_count, contact_count, favorite_count, avg_rating, updated_at,
        images, locality, bedrooms, bathrooms, furnishing, area
    """
    
    if query.q:
        select_fields += ", ts_rank(search_vector, to_tsquery('english', :q_fts)) as ts_rank_score"
    
    where_str = " AND ".join(where_clauses)
    
    # Execute query
    try:
        raw_sql = f"SELECT {select_fields} FROM search.property_index WHERE {where_str}"
        # We fetch all matching (or a reasonable large limit) to rank them in memory
        raw_sql += " LIMIT 500"
        
        rows = db.execute(text(raw_sql), sql_params).fetchall()
        
        properties = []
        text_relevance_scores = {}
        for row in rows:
            # Safe parsing for images & amenities
            images_raw = row[20] or ""
            images_list = [img.strip() for img in images_raw.split(",") if img.strip()]
            
            amenities_raw = row[10] or ""
            amenities_list = [am.strip() for am in amenities_raw.split(",") if am.strip()]
 
            prop = {
                "id": row[0],
                "property_id": row[0],
                "title": row[1] or "Untitled Property",
                "description": row[2] or "",
                "address": row[3] or "",
                "city": row[4] or "",
                "state": row[5] or "",
                "property_type": row[6] or "Apartment",
                "price": row[7] or 0.0,
                "lat": row[8] or 0.0,
                "lng": row[9] or 0.0,
                "amenities": amenities_list,
                "is_featured": row[11] or False,
                "is_verified": row[12] or False,
                "owner_verified": row[13] or False,
                "media_count": row[14] or 0,
                "view_count": row[15] or 0,
                "contact_count": row[16] or 0,
                "favorite_count": row[17] or 0,
                "avg_rating": row[18] or 0.0,
                "updated_at": str(row[19]) if row[19] else None,
                "images": images_list,
                "locality": row[21] or "",
                "bedrooms": row[22] or 0,
                "bathrooms": row[23] or 0,
                "furnishing": row[24] or "",
                "area": row[25] or ""
            }
            if query.q and len(row) > 26:
                text_relevance_scores[prop["property_id"]] = float(row[26] or 0)
            properties.append(prop)
            
        # Rank them
        ranked = rank_properties(properties, text_relevance_scores, query.ranking_profile)
        
        # Paginate
        total = len(ranked)
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        paginated = ranked[start_idx:end_idx]
        
        took = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=paginated,
            total=total,
            page=query.page,
            page_size=query.page_size,
            took_ms=took
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search engine error")

@app.get("/search/autocomplete", response_model=AutocompleteResponse)
def autocomplete(
    q: str,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    suggestions = get_autocomplete_suggestions(q, db, user_id=user_id)
    trending = get_trending_searches()
    return AutocompleteResponse(suggestions=suggestions, trending=trending)

@app.get("/search/trending")
def trending_searches():
    return {"trending": get_trending_searches()}

@app.get("/search/contextual")
def contextual_suggestions(office: Optional[str] = None, locality: Optional[str] = None):
    return {"suggestions": get_contextual_suggestions(office, locality)}

@app.post("/search/track")
def track_analytics_event(
    event: TrackEventRequest,
    request: Request
):
    user_id = get_current_user_id(request)
    ip = request.client.host if request.client else None
    
    if event.event_type == "property_viewed" and event.property_id:
        track_property_view(event.property_id, user_id=user_id, ip=ip, source=event.source or "unknown")
    elif event.event_type == "search_performed" and event.search_query:
        track_search(event.search_query, event.filters or {}, event.result_count or 0, user_id=user_id, ip=ip)
    else:
        track_event(
            f"analytics.{event.event_type}",
            payload=event.model_dump(exclude_none=True, exclude={"event_type"}),
            user_id=user_id,
            ip=ip
        )
    return {"status": "tracked"}

@app.get("/recommendations/similar/{property_id}")
def similar_properties(property_id: int, db: Session = Depends(get_db)):
    return {"results": get_similar_properties(property_id, db)}

@app.get("/recommendations/for-you")
def recommendations_for_you(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return {"results": get_trending_in_locality("", db, limit=8)} # Fallback
    return {"results": get_recommendations_for_user(user_id, db)}

@app.get("/recommendations/trending/{locality}")
def trending_in_locality(locality: str, db: Session = Depends(get_db)):
    return {"results": get_trending_in_locality(locality, db)}

@app.get("/recommendations/office/{office_name}")
def office_commute_recommendations(office_name: str, max_min: int = 30, db: Session = Depends(get_db)):
    return {"results": get_commute_recommendations(office_name, db, max_commute_min=max_min)}

@app.get("/recommendations/people-also-viewed/{property_id}")
def people_also_viewed(property_id: int, db: Session = Depends(get_db)):
    return {"results": get_people_also_viewed(property_id, db)}

@app.get("/search/semantic")
def semantic_search_api(q: str, limit: int = 10, db: Session = Depends(get_db)):
    return {"results": semantic_search(q, db, limit=limit)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("search_service.main:app", host="0.0.0.0", port=8015, reload=True)
