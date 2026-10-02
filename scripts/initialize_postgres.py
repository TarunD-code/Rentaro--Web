import sys
import os
import logging

# Add root folder to path so we can import shared_database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("initialize_postgres")

schemas = [
    "auth",
    "profile",
    "property",
    "payment",
    "maintenance",
    "onboarding",
    "agreements",
    "billing",
    "owner_dashboard",
    "subscriptions",
    "support",
    "notifications",
    "communication",
    "search"
]

def initialize_database():
    logger.info("Connecting to PostgreSQL to initialize database...")
    if not shared_database.sync_engine:
        logger.error("Sync Engine is not initialized! Ensure PostgreSQL is running.")
        return False
        
    try:
        with shared_database.sync_engine.connect() as conn:
            from sqlalchemy import text
            # Enable PostGIS extension
            logger.info("Enabling PostGIS extension...")
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
                logger.info("PostGIS extension successfully initialized!")
            except Exception as e:
                logger.warning(f"Could not enable PostGIS extension (perhaps not running as superuser or missing): {e}")
            
            # Create all schemas
            for schema in schemas:
                logger.info(f"Creating schema if not exists: {schema}...")
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.commit()
                
            logger.info("Database schemas initialization completed successfully!")
            return True
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False

if __name__ == "__main__":
    initialize_database()
