import os
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
import shared_database

# ─────────────────────────────────────────────────────────────
# KYC Schema Isolation
# All KYC tables live in the "kyc" PostgreSQL schema to
# enforce logical separation from other service data.
# ─────────────────────────────────────────────────────────────
schema_metadata = MetaData(schema="kyc")
Base = declarative_base(metadata=schema_metadata)

engine = shared_database.sync_engine
SessionLocal = shared_database.SyncSessionLocal


def get_db():
    """Sync database session dependency for FastAPI endpoints."""
    if not SessionLocal:
        raise RuntimeError("PostgreSQL Sync SessionLocal is not initialized")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
