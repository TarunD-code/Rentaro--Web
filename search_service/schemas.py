from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchQuery(BaseModel):
    q: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_type: Optional[str] = None
    bhk: Optional[str] = None
    furnished: Optional[bool] = None
    pet_friendly: Optional[bool] = None
    locality_score_min: Optional[float] = None
    commute_score_min: Optional[float] = None
    near_lat: Optional[float] = None
    near_lng: Optional[float] = None
    radius_km: Optional[float] = 5.0
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lng: Optional[float] = None
    max_lng: Optional[float] = None
    metro_corridor: Optional[str] = None
    office_hub: Optional[str] = None
    sort_by: str = "relevance"
    ranking_profile: str = "default"
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=20, ge=1, le=50)


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    took_ms: float
    fallback_used: bool = False

class AutocompleteResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    trending: List[Dict[str, Any]]

class TrackEventRequest(BaseModel):
    event_type: str
    property_id: Optional[int] = None
    search_query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    result_count: Optional[int] = None
    position: Optional[int] = None
    dwell_seconds: Optional[int] = None
    source: Optional[str] = None
