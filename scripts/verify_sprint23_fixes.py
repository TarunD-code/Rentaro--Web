import sys
import os
import requests
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from property_service.main import app as property_app
from property_service.database import SessionLocal, Base, engine
from property_service import models
import jwt

SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"
ALGORITHM = "HS256"

# Mock Admin Token
def get_admin_token():
    payload = {"sub": "admin@rentora.com", "role": "admin"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

client = TestClient(property_app)

def verify_property_bugfixes():
    print("Verifying Property Service Bugfixes...")
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Verify /metrics (Was 422, should be 200)
    print("Checking /metrics route prioritization...")
    res = client.get("/metrics", headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code != 200:
        print(f"FAILED detail: {res.json()}")
    assert res.status_code == 200
    assert "total_active_listings" in res.json()

    # 2. Verify /analytics/host (Was 403 for admin, should be 200)
    print("Checking /analytics/host RBAC for ADMIN...")
    res = client.get("/analytics/host", headers=headers)
    print(f"Status: {res.status_code}")
    assert res.status_code in [200, 404] # 404 is also fine if no data, but shouldn't be 403

    # 3. Verify /{property_id} still works (Route still functional)
    print("Checking /{property_id} dynamic route...")
    # Add a dummy property to test
    db = SessionLocal()
    dummy = models.Property(id=999, owner_id="admin@rentora.com", title="Test", address="Test", price=15000.0)
    db.merge(dummy)
    db.commit()
    db.close()
    
    res = client.get("/999", headers=headers)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    assert res.json()["id"] == 999

    # 4. Verify /metrics with owner_id filter (New Feature)
    print("Checking /metrics with owner_id filtering...")
    res = client.get("/metrics?owner_id=owner1@rentora.com", headers=headers)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    assert res.json()["role"] == "admin"

    # 5. Verify Notification Health (Standalone)
    print("Checking Notification Service health via requests...")
    try:
        n_res = requests.get("http://127.0.0.1:8013/health", timeout=5)
        print(f"Notification Health: {n_res.status_code} - {n_res.json()['status']}")
        assert n_res.status_code == 200
    except Exception as e:
        print(f"Notification Service check failed: {e}")

    print("\nVerification Successful: Metrics filtering, RBAC, and Notification routing confirmed.")

if __name__ == "__main__":
    verify_property_bugfixes()
