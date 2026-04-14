from pydantic import BaseModel, root_validator
from typing import Optional, List
import datetime

class PropertyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    address: str
    property_type: Optional[str] = "Apartment"
    price: float
    amenities: Optional[str] = None # e.g. "Pool, Gym, Parking"

class MediaItem(BaseModel):
    id: int
    type: str # image, video
    url: str
    thumbnailUrl: Optional[str]
    mime: Optional[str]
    size: Optional[int]

    class Config:
        orm_mode = True

class PropertyMediaOut(MediaItem): # Compatibility with previous code
    pass

class HostProfile(BaseModel):
    id: str
    name: str
    verified: bool
    responseTime: str

class GeoLocation(BaseModel):
    lat: Optional[float]
    lng: Optional[float]

class AddressDetail(BaseModel):
    city: Optional[str]
    state: Optional[str]
    country: str = "India"
    geo: Optional[GeoLocation]

class PropertyOut(BaseModel): # Listing card view
    id: int
    owner_id: str
    title: str
    description: Optional[str]
    address: str
    property_type: Optional[str] = "Apartment"
    price: float
    amenities: Optional[str]
    commute_score: Optional[float]
    created_at: datetime.datetime
    media: List[MediaItem] = []

    class Config:
        orm_mode = True

class PropertyDetail(BaseModel): # Full detail view
    id: int
    title: str
    description: Optional[str]
    price: float
    currency: str = "INR"
    property_type: Optional[str] = "Apartment"
    address: AddressDetail
    amenities: List[str]
    commute_score: Optional[float]
    average_rating: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    media: List[MediaItem]
    host: HostProfile
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

    class Config:
        orm_mode = True

class ReviewCreate(BaseModel):
    rating: float
    text: Optional[str] = None

class ReviewOut(BaseModel):
    id: int
    reviewer_id: str
    rating: float
    text: Optional[str]
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class HostAnalyticsOut(BaseModel):
    total_views: int
    total_inquiries: int
    total_favorites: int
    average_rating: float

class DashboardMetricsOut(BaseModel):
    total_active_listings: int
    total_views: int
    total_applications: int
    pending_rent: float
    role: str

    model_config = {"from_attributes": True}

class VisitRequestCreate(BaseModel):
    property_id: int
    requested_slot: datetime.datetime

class VisitRequestUpdate(BaseModel):
    status: Optional[str] = None
    owner_response: Optional[str] = None

class VisitRequestOut(BaseModel):
    id: int
    property_id: int
    tenant_id: str
    owner_id: str
    requested_slot: datetime.datetime
    status: str
    owner_response: Optional[str]
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class RentalAgreementCreate(BaseModel):
    property_id: int
    tenant_id: str
    metadata_json: Optional[str] = None

class RentalAgreementUpdate(BaseModel):
    status: Optional[str] = None
    pdf_url: Optional[str] = None
    signnow_id: Optional[str] = None

class RentalAgreementOut(BaseModel):
    id: int
    property_id: int
    tenant_id: str
    owner_id: str
    status: str
    pdf_url: Optional[str]
    signnow_id: Optional[str]
    document_hash: Optional[str]
    signed_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    class Config:
        orm_mode = True

