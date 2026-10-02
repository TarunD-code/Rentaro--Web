import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base

# Setup centralized logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shared_database")

# Load .env file manually into os.environ if it exists
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    logger.info("Loading environment configurations from .env")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Target connection URLs
DEFAULT_ASYNC_URL = "postgresql+asyncpg://postgres:rentora_secure_password@postgres:5432/rentora"
DEFAULT_DATABASE_URL = "postgresql://postgres:rentora_secure_password@postgres:5432/rentora"

DATABASE_ASYNC_URL = os.environ.get("DATABASE_ASYNC_URL", DEFAULT_ASYNC_URL)
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "RENTORA_SUPER_SECRET_KEY")

# Automatically align async database url host with sync database url host if inside docker
if DATABASE_URL and "@postgres:" in DATABASE_URL and "@localhost:" in DATABASE_ASYNC_URL:
    DATABASE_ASYNC_URL = DATABASE_ASYNC_URL.replace("@localhost:", "@postgres:")

logger.info(f"Database Async URL: {DATABASE_ASYNC_URL}")
logger.info(f"Database Sync URL: {DATABASE_URL}")

# Setup core engines with connection pools
try:
    async_engine = create_async_engine(
        DATABASE_ASYNC_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False
    )
    logger.info("SQLAlchemy Async Engine created successfully with pool_size=20")
except Exception as e:
    logger.error(f"Failed to create Async Engine: {e}")
    async_engine = None

try:
    # Clean currentSchema from sync connection string if present (psycopg2 incompatibility)
    sync_db_url = DATABASE_URL
    if "?" in sync_db_url:
        base_part, query_part = sync_db_url.split("?", 1)
        params = [p for p in query_part.split("&") if not p.startswith("currentSchema=")]
        if params:
            sync_db_url = base_part + "?" + "&".join(params)
        else:
            sync_db_url = base_part

    sync_engine = create_engine(
        sync_db_url,
        pool_size=10,
        pool_pre_ping=True,
        echo=False
    )
    logger.info("SQLAlchemy Sync Engine created successfully with pool_size=10")
except Exception as e:
    logger.error(f"Failed to create Sync Engine: {e}")
    sync_engine = None

# Async & Sync Session factories
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
) if async_engine else None

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
) if sync_engine else None

# Backward compatibility exports
engine = sync_engine
SessionLocal = SyncSessionLocal

# Helper dependency generators
async def get_async_db():
    if not AsyncSessionLocal:
        raise RuntimeError("AsyncSessionLocal is not initialized")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

def get_sync_db():
    if not SyncSessionLocal:
        raise RuntimeError("SyncSessionLocal is not initialized")
    session = SyncSessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_metadata_for_schema(schema_name: str) -> MetaData:
    """Returns MetaData configured for a specific Postgres schema."""
    return MetaData(schema=schema_name)
