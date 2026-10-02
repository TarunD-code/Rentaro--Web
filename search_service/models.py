from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, BigInteger
from sqlalchemy.sql import func
from .database import Base

class PropertyIndex(Base):
    __tablename__ = "property_index"
    __table_args__ = {"schema": "search"}

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text)
    address = Column(Text)
    city = Column(String(128))
    state = Column(String(128))
    area = Column(String(128))
    property_type = Column(String(64))
    price = Column(Float)
    lat = Column(Float)
    lng = Column(Float)
    amenities = Column(Text)
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_furnished = Column(Boolean, default=False)
    is_pet_friendly = Column(Boolean, default=False)
    owner_verified = Column(Boolean, default=False)
    locality_score = Column(Float, default=0)
    commute_score = Column(Float, default=0)
    metro_score = Column(Float, default=0)
    hospital_score = Column(Float, default=0)
    school_score = Column(Float, default=0)
    walkability_score = Column(Float, default=0)
    popularity_score = Column(Float, default=0)
    view_count = Column(Integer, default=0)
    contact_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0)
    media_count = Column(Integer, default=0)
    tags = Column(Text)
    status = Column(String(32), default='available')
    images = Column(Text)
    locality = Column(String(256))
    bedrooms = Column(Integer, default=0)
    bathrooms = Column(Integer, default=0)
    furnishing = Column(String(64))
    # embedding vector(384) not directly mapped in SQLAlchemy base, handled via raw SQL
    indexed_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AutocompleteIndex(Base):
    __tablename__ = "autocomplete_index"
    __table_args__ = {"schema": "search"}

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(256), nullable=False)
    term_type = Column(String(64), nullable=False)
    display_name = Column(String(512))
    lat = Column(Float)
    lng = Column(Float)
    search_count = Column(Integer, default=0)

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = {"schema": "search"}

    id = Column(BigInteger, primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)
    user_id = Column(String(256), index=True)
    session_id = Column(String(256))
    property_id = Column(Integer, index=True)
    search_query = Column(Text)
    filters_json = Column(Text)
    result_count = Column(Integer)
    position_clicked = Column(Integer)
    dwell_seconds = Column(Integer)
    ip_hash = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())

class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = {"schema": "search"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(256), nullable=False, index=True)
    query = Column(Text, nullable=False)
    filters_json = Column(Text)
    result_count = Column(Integer)
    searched_at = Column(DateTime, server_default=func.now())
