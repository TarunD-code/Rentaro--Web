import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:rentora_secure_password@postgres:5432/rentora"
)

# Strip currentSchema from connection string (psycopg2 incompatibility)
if "?" in DATABASE_URL:
    base_part, query_part = DATABASE_URL.split("?", 1)
    params = [p for p in query_part.split("&") if not p.startswith("currentSchema=")]
    if params:
        DATABASE_URL = base_part + "?" + "&".join(params)
    else:
        DATABASE_URL = base_part

engine = create_engine(DATABASE_URL, pool_size=10, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
