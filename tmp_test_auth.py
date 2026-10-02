import sys
import os

from fastapi.testclient import TestClient

print("Attempting to import auth_service.main")
try:
    from auth_service.main import app
    print("Import successful. Creating TestClient.")
    client = TestClient(app)
    
    print("Sending POST /auth/login with correct payload")
    response = client.post("/auth/login", json={"email_or_phone": "admin@rentaro.com", "password": "admin123"})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error during import or request: {e}")
    import traceback
    traceback.print_exc()
