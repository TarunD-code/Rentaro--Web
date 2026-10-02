"""
Unit & Integration Tests for KYC Service
=======================================

Run: python -m pytest tests/test_kyc_service.py -v
"""

import sys
import os
import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyc_service.database import SessionLocal, engine, Base
from kyc_service import models, encryption, schemas
from kyc_service.main import app
from kyc_service.security import KYC_WEBHOOK_SECRET, SECRET_KEY, ALGORITHM

# ─────────────────────────────────────────────────────────────
# Test Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    import kyc_service.database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import OperationalError

    # 1. Try connecting to the default PostgreSQL engine
    try:
        if kyc_service.database.engine:
            with kyc_service.database.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS kyc"))
                conn.commit()
            Base.metadata.create_all(bind=kyc_service.database.engine)
            session = SessionLocal()
            yield session
            session.close()
            return
    except (OperationalError, Exception) as e:
        print(f"\n⚠️ PostgreSQL offline ({e}). Falling back to SQLite for tests.")

    # 2. SQLite fallback for local test execution
    from sqlalchemy import event
    sqlite_url = "sqlite:///./rentora_kyc_test.db"
    test_engine = create_engine(sqlite_url)

    @event.listens_for(test_engine, "connect")
    def connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("ATTACH DATABASE './rentora_kyc_test_schema.db' AS kyc")
        cursor.close()
    
    # Patch database engine/session references
    kyc_service.database.engine = test_engine
    kyc_service.database.SessionLocal = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
    
    # Create tables locally inside attached kyc DB schema
    Base.metadata.create_all(bind=test_engine)
    
    session = kyc_service.database.SessionLocal()
    yield session
    session.close()

    # Clean up test DB files
    for filename in ["./rentora_kyc_test.db", "./rentora_kyc_test_schema.db"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass


@pytest.fixture
def client():
    return TestClient(app)


# ─────────────────────────────────────────────────────────────
# 1. Encryption Engine & Masking Helper Tests
# ─────────────────────────────────────────────────────────────

class TestEncryptionEngine:
    def test_fernet_encryption_decryption(self):
        engine = encryption.cipher_engine
        plaintext = "123456781234"
        
        # Test encrypt
        ciphertext = engine.encrypt(plaintext)
        assert isinstance(ciphertext, bytes)
        assert ciphertext != plaintext.encode()
        
        # Test decrypt
        decrypted = engine.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_aadhaar_masking(self):
        engine = encryption.cipher_engine
        assert engine.mask_aadhaar("123456781234") == "XXXX-XXXX-1234"
        assert engine.mask_aadhaar("1234 5678 9012") == "XXXX-XXXX-9012"
        assert engine.mask_aadhaar("") == ""
        assert engine.mask_aadhaar("123") == "XXXX-XXXX-XXXX"

    def test_pan_masking(self):
        engine = encryption.cipher_engine
        assert engine.mask_pan("ABCDE1234F") == "XXXXXX234F"
        assert engine.mask_pan("") == ""
        assert engine.mask_pan("ABC") == "XXXXXXXXXX"


# ─────────────────────────────────────────────────────────────
# 2. Database Models envelope encryption hybrid property tests
# ─────────────────────────────────────────────────────────────

class TestKYCDatabaseModels:
    def test_kyc_record_hybrid_properties(self, db):
        # Create a KYCRecord
        record = models.KYCRecord(
            user_id="test_user_encryption",
            status=models.KYCStatus.PENDING,
            transaction_token="TOKEN-123"
        )
        # Write Aadhaar/PAN through hybrid setters
        record.aadhaar_number = "987654321012"
        record.pan_number = "XYZAB9876Q"
        
        db.add(record)
        db.commit()
        db.refresh(record)

        # 1. Assert decrypted getter works
        assert record.aadhaar_number == "987654321012"
        assert record.pan_number == "XYZAB9876Q"

        # 2. Assert database columns hold ENCRYPTED values (bytes), not plaintext
        # Bypass cache/session references to read raw properties
        db.expire(record)
        db_record = db.query(models.KYCRecord).filter(models.KYCRecord.id == record.id).first()
        
        assert db_record.encrypted_aadhaar is not None
        assert db_record.encrypted_pan is not None
        assert isinstance(db_record.encrypted_aadhaar, bytes)
        assert isinstance(db_record.encrypted_pan, bytes)
        
        # Plaintext must not exist in columns
        assert "987654321012" not in str(db_record.encrypted_aadhaar)
        assert "XYZAB9876Q" not in str(db_record.encrypted_pan)

        # 3. Assert pre-computed masked values exist in columns
        assert db_record.masked_aadhaar == "XXXX-XXXX-1012"
        assert db_record.masked_pan == "XXXXXX876Q"

        # Clean up
        db.delete(record)
        db.commit()



# ─────────────────────────────────────────────────────────────
# 3. Webhook signature & API client endpoint tests
# ─────────────────────────────────────────────────────────────

class TestKYCAPIEndpoints:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_initiate_kyc_unauthorized(self, client):
        # Missing JWT authorization header
        response = client.post("/api/v1/kyc/initiate")
        assert response.status_code == 401

    def test_status_unauthorized(self, client):
        # Missing JWT authorization header
        response = client.get("/api/v1/kyc/status")
        assert response.status_code == 401

    def test_initiate_and_webhook_workflow(self, client, db):
        import jwt
        # 1. Generate active test JWT token
        payload = {"sub": "test_user_flow@rentora.com"}
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        headers = {"Authorization": f"Bearer {jwt_token}"}

        # 2. Initiate KYC
        init_res = client.post("/api/v1/kyc/initiate", headers=headers)
        assert init_res.status_code == 200
        init_data = init_res.json()
        token = init_data["transaction_token"]
        assert token.startswith("RNT-KYC-")
        assert "checkout_url" in init_data

        # 3. Verify record was created in database
        db_record = db.query(models.KYCRecord).filter(models.KYCRecord.transaction_token == token).first()
        assert db_record is not None
        assert db_record.status == models.KYCStatus.PENDING

        # 4. Trigger Webhook Callback with HMAC Signature
        webhook_payload = {
            "transaction_token": token,
            "status": "VERIFIED",
            "aadhaar_number": "112233445566",
            "pan_number": "PQRMN1122Z",
            "facial_score": 0.954,
            "vendor_reference_id": "VEND-REF-999"
        }
        
        # Calculate webhook signature using exact compact JSON representation
        payload_bytes = json.dumps(webhook_payload, separators=(',', ':')).encode("utf-8")
        sig = hmac.new(
            KYC_WEBHOOK_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Call Webhook with calculated signature and content-type header
        webhook_headers = {
            "X-Webhook-Signature": sig,
            "Content-Type": "application/json"
        }
        web_res = client.post("/api/v1/kyc/webhook", content=payload_bytes, headers=webhook_headers)
        assert web_res.status_code == 200
        assert web_res.json()["received"] is True

        # 5. Query status endpoint and check response schemas (PII should be masked only)
        status_res = client.get("/api/v1/kyc/status", headers=headers)
        assert status_res.status_code == 200
        status_data = status_res.json()
        
        assert status_data["status"] == "VERIFIED"
        assert status_data["masked_aadhaar"] == "XXXX-XXXX-5566"
        assert status_data["masked_pan"] == "XXXXXX122Z"
        assert status_data["facial_match_score"] == 0.954
        assert "verified_at" in status_data

        # Clean up database entry
        db_record = db.query(models.KYCRecord).filter(models.KYCRecord.transaction_token == token).first()
        if db_record:
            db.delete(db_record)
            db.commit()

    def test_webhook_invalid_signature(self, client):
        webhook_payload = {
            "transaction_token": "RNT-KYC-MOCKTOKEN",
            "status": "VERIFIED"
        }
        webhook_headers = {"X-Webhook-Signature": "wrongsignaturevalue"}
        res = client.post("/api/v1/kyc/webhook", json=webhook_payload, headers=webhook_headers)
        # Should raise 403 Forbidden with zero details leaked
        assert res.status_code == 403
        assert "Invalid Webhook Signature" in res.text

    def test_simulation_endpoint(self, client, db):
        import jwt
        # 1. Generate active test JWT token
        payload = {"sub": "test_user_sim@rentora.com"}
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        headers = {"Authorization": f"Bearer {jwt_token}"}

        # 2. Initiate KYC
        init_res = client.post("/api/v1/kyc/initiate", headers=headers)
        token = init_res.json()["transaction_token"]

        # 3. Run developer simulation endpoint (no signature header required)
        sim_payload = {
            "transaction_token": token,
            "status": "VERIFIED",
            "aadhaar_number": "999988887777",
            "pan_number": "ABCDE9999F",
            "facial_score": 0.88,
            "vendor_reference_id": "SIM-REF-111"
        }
        sim_res = client.post("/api/v1/kyc/simulate-webhook", json=sim_payload, headers=headers)
        assert sim_res.status_code == 200
        assert sim_res.json()["received"] is True
        assert sim_res.json()["status"] == "VERIFIED"

        # 4. Verify DB was updated
        db_record = db.query(models.KYCRecord).filter(models.KYCRecord.transaction_token == token).first()
        assert db_record.status == models.KYCStatus.VERIFIED
        assert db_record.aadhaar_number == "999988887777"
        assert db_record.masked_aadhaar == "XXXX-XXXX-7777"

        # Clean up database entry
        db.delete(db_record)
        db.commit()
