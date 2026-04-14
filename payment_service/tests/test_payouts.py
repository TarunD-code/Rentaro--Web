import pytest
from fastapi.testclient import TestClient
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from payment_service.main import app
from payment_service import models
from payment_service.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user_info():
    # Return mocked owner info
    return {"sub": "owner_123", "role": "owner"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[app.dependency_overrides.get("get_current_user_info", None) or get_db] = override_get_current_user_info
# For tests, we explicitly just replace the dependency by inspecting app requirements
# Note: In actual code `get_current_user_info` is used. We can patch it since we know its name.

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@patch('payment_service.main.get_current_user_info')
@patch('payment_service.razorpay_client.razorpay_client.create_payout')
def test_initiate_payout(mock_payout, mock_user):
    mock_user.return_value = {"sub": "owner_123", "role": "owner"}
    app.dependency_overrides[list(app.dependency_overrides.keys())[1]] = lambda: {"sub": "owner_123", "role": "owner"}
    
    mock_payout.return_value = {"id": "pout_test123"}

    # Pre-fund owner balance
    db = TestingSessionLocal()
    db.add(models.OwnerBalance(owner_id="owner_123", available_balance=50000.0))
    db.commit()
    db.close()

    res = client.post("/payouts/initiate", json={
        "amount": 10000.0,
        "fund_account_id": "fa_123"
    })

    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == 10000.0
    assert data["status"] == "pending"
    assert data["razorpay_payout_id"] == "pout_test123"

@patch('payment_service.main.get_current_user_info')
def test_initiate_payout_insufficient_funds(mock_user):
    app.dependency_overrides[list(app.dependency_overrides.keys())[1]] = lambda: {"sub": "owner_123", "role": "owner"}

    db = TestingSessionLocal()
    db.add(models.OwnerBalance(owner_id="owner_123", available_balance=500.0))
    db.commit()
    db.close()

    res = client.post("/payouts/initiate", json={
        "amount": 10000.0, # $>500
        "fund_account_id": "fa_123"
    })

    assert res.status_code == 400
    assert "Insufficient available balance" in res.json()["detail"]


@patch('payment_service.main.get_current_user_info')
def test_cancel_payout(mock_user):
    app.dependency_overrides[list(app.dependency_overrides.keys())[1]] = lambda: {"sub": "owner_123", "role": "owner"}

    db = TestingSessionLocal()
    db.add(models.OwnerBalance(owner_id="owner_123", available_balance=4000.0))
    db.add(models.Payout(id=1, owner_id="owner_123", amount=1000.0, status="pending"))
    db.commit()
    db.close()

    res = client.post("/payouts/1/cancel")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cancelled"

    db = TestingSessionLocal()
    bal = db.query(models.OwnerBalance).first()
    # It refunded 1000, so Should be 5000
    assert bal.available_balance == 5000.0
    db.close()
