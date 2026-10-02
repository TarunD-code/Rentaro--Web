from fastapi.testclient import TestClient
import pytest
from .main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_no_auth():
    response = client.post("/register", json={"device_token": "test_token", "platform": "android"})
    assert response.status_code == 401 # Should fail without bearer token
