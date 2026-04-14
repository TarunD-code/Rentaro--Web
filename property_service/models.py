from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, index=True) # References user_identifier
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=False) # Full address
    property_type = Column(String, default="Apartment")
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, default="India")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    amenities = Column(String, nullable=True) # Stored as comma separated string for MVP
    is_featured = Column(Boolean, default=False)
    commute_score = Column(Float, nullable=True) # Normalized 1-10 string mapped score
    status = Column(String, default="available")  # available, occupied, maintenance, unlisted
    available_from = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    media = relationship("PropertyMedia", back_populates="property")

class PropertyMedia(Base):
    __tablename__ = "property_media"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    file_type = Column(String) # image, video
    raw_url = Column(String) # Raw S3/CDN URL
    thumb_url = Column(String, nullable=True) # Thumbnail URL
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True) # in bytes
    width = Column(Integer, nullable=True) # in pixels
    height = Column(Integer, nullable=True)
    
    property = relationship("Property", back_populates="media")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    reviewer_id = Column(String, index=True) # user_identifier from profile/auth
    rating = Column(Float, nullable=False) # 1.0 to 5.0
    text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class VisitRequest(Base):
    __tablename__ = "visit_requests"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    tenant_id = Column(String, index=True)
    owner_id = Column(String, index=True)
    requested_slot = Column(DateTime, nullable=False)
    status = Column(String, default="pending") # pending, confirmed, rescheduled, cancelled
    owner_response = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RentalAgreement(Base):
    __tablename__ = "rental_agreements"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    tenant_id = Column(String, index=True)
    owner_id = Column(String, index=True)
    status = Column(String, default="draft") # draft, pending_signatures, signed, active, expired
    pdf_url = Column(String, nullable=True)
    signnow_id = Column(String, nullable=True)
    document_hash = Column(String, nullable=True)
    metadata_json = Column(String, nullable=True) # JSON dump of extra terms
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

