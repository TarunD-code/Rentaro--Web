from pydantic import BaseModel
from typing import List, Optional
import datetime

class MetricOut(BaseModel):
    id: int
    property_id: int
    period_start: datetime.datetime
    revenue_total: float
    occupancy_count: int
    pending_rent_total: float
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class MetricsSummary(BaseModel):
    revenue_total: float
    pending_rent_total: float
    occupancy_rate: float
    history: List[MetricOut]

class ReportOut(BaseModel):
    id: int
    report_type: str
    report_path: str
    status: str
    generated_at: datetime.datetime

    class Config:
        from_attributes = True
