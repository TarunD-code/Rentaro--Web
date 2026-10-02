import sys
import os
import bcrypt
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from auth_service.main import app
from auth_service import models
from auth_service.database import Base, engine, SessionLocal, get_db

client = TestClient(app)

def verify_fix():
    print("Verifying Auth Fix...")
    
    # Setup test user in DB
    db = SessionLocal()
    # Cleanup if exists
    db.query(models.User).filter(models.User.email_or_phone == "verify@rentora.com").delete()
    db.commit()
    
    hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = models.User(
        email_or_phone="verify@rentora.com",
        hashed_password=hashed_password,
        role="tenant",
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.close()

    # 1. Test Incorrect Email
    print("Testing incorrect email...")
    res = client.post("/auth/login", json={"email_or_phone": "wrong@rentora.com", "password": "any"})
    print(f"Status: {res.status_code}, Detail: {res.json()['detail']}")
    assert res.json()['detail'] == "Invalid credentials"

    # 2. Test Incorrect Password
    print("Testing incorrect password...")
    res = client.post("/auth/login", json={"email_or_phone": "verify@rentora.com", "password": "wrong"})
    print(f"Status: {res.status_code}, Detail: {res.json()['detail']}")
    assert res.json()['detail'] == "Invalid credentials"

    # 3. Test Success
    print("Testing success...")
    res = client.post("/auth/login", json={"email_or_phone": "verify@rentora.com", "password": "password123"})
    print(f"Status: {res.status_code}, Role: {res.json().get('role')}")
    assert res.status_code == 200

    print("\nVerification Successful: Logic correctly distinguishes failures and returns accurate messages.")

if __name__ == "__main__":
    verify_fix()
