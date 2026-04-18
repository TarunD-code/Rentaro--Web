from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class OwnerMetric(Base):
    __tablename__ = "owner_metrics"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, index=True)
    property_id = Column(Integer, index=True)
    period_start = Column(DateTime) # Month start
    revenue_total = Column(Float, default=0.0)
    occupancy_count = Column(Integer, default=0) # 1 if occupied, 0 if available
    pending_rent_total = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class OwnerReport(Base):
    __tablename__ = "owner_reports"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, index=True)
    report_type = Column(String) # revenue, occupancy
    report_path = Column(String) # Local path to PDF
    status = Column(String, default="generated") # generating, generated, failed
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
