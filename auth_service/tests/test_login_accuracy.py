import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

from ..main import app, get_current_user_info
from ..database import Base, get_db
from .. import models

# Use an in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_accuracy.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create a test user
    hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = models.User(
        email_or_phone="test@rentora.com",
        hashed_password=hashed_password,
        role="tenant",
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.close()

def test_login_success():
    response = client.post("/auth/login", json={
        "email_or_phone": "test@rentora.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_user():
    response = client.post("/auth/login", json={
        "email_or_phone": "nonexistent@rentora.com",
        "password": "password123"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_invalid_password():
    response = client.post("/auth/login", json={
        "email_or_phone": "test@rentora.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_unverified_user():
    db = TestingSessionLocal()
    hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = models.User(
        email_or_phone="unverified@rentora.com",
        hashed_password=hashed_password,
        role="tenant",
        is_verified=False
    )
    db.add(user)
    db.commit()
    
    response = client.post("/auth/login", json={
        "email_or_phone": "unverified@rentora.com",
        "password": "password123"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not verified"
