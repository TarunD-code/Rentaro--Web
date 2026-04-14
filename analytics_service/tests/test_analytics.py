import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from analytics_service.main import app
from analytics_service.database import Base, get_db
from analytics_service import models

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def mock_get_current_admin():
    return {"sub": "admin_1", "role": "admin"}


app.dependency_overrides[app.dependency_overrides.get("get_current_admin", None) or get_db] = mock_get_current_admin
# Override the actual dependency from main
from analytics_service.main import get_current_admin
app.dependency_overrides[get_current_admin] = mock_get_current_admin


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_get_analytics_summary_empty():
    res = client.get("/admin/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] == 0.0
    assert data["occupancy_rate_30d"] == 0.0

def test_get_analytics_summary_populated():
    import datetime
    db = TestingSessionLocal()
    snapshot = models.DailyAggregateSnapshot(
        report_date=datetime.datetime.utcnow(),
        total_revenue=250000.0,
        pending_payouts_volume=45000.0,
        occupancy_rate=92.0
    )
    db.add(snapshot)
    db.commit()
    db.close()

    res = client.get("/admin/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] == 250000.0
    assert data["pending_payouts"] == 45000.0
    assert data["occupancy_rate_30d"] == 0.92

def test_export_report_audit():
    res = client.get("/admin/analytics/export?type=pdf")
    assert res.status_code == 200
    assert "PDF report" in res.json()["message"]
    
    db = TestingSessionLocal()
    audit = db.query(models.AuditLog).first()
    assert audit is not None
    assert audit.admin_id == "admin_1"
    assert audit.action == "download_report_pdf"
    db.close()
