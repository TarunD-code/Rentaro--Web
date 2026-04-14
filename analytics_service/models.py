from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base
import datetime

class DailyAggregateSnapshot(Base):
    """
    Acts as a materialized view refreshed nightly detailing daily key performance indicators.
    """
    __tablename__ = "daily_aggregate_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(DateTime, nullable=False, unique=True, index=True) # e.g. 2026-04-14 00:00:00
    
    # Platform metrics
    total_revenue = Column(Float, default=0.0)
    pending_payouts_volume = Column(Float, default=0.0)
    failed_refunds_volume = Column(Float, default=0.0)
    total_active_mandates = Column(Integer, default=0)
    
    # Occupancy
    total_properties = Column(Integer, default=0)
    occupied_properties = Column(Integer, default=0)
    occupancy_rate = Column(Float, default=0.0) # Percentage 0-100
    
    # SLA Maintenance
    total_open_maintenance = Column(Integer, default=0)
    total_overdue_maintenance = Column(Integer, default=0)
    avg_resolution_time_hours = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AuditLog(Base):
    """Tracks sensitive admin actions (e.g. reporting downloads, dispute manual resolve)"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String, nullable=False, index=True) # ID from auth_service
    action = Column(String, nullable=False) # e.g., "downloaded_monthly_report", "resolved_ledger_dispute"
    target_entity = Column(String, nullable=True) # e.g., "owner_123_statements"
    details = Column(String, nullable=True) # JSON dump of parameters
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
