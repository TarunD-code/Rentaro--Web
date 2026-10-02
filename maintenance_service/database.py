"""
Rentora Maintenance Service — Database Configuration
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
import shared_database

# Centralized Postgres Schema Isolation
schema_metadata = MetaData(schema="maintenance")
Base = declarative_base(metadata=schema_metadata)

engine = shared_database.sync_engine
SessionLocal = shared_database.SyncSessionLocal

def get_db():
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

