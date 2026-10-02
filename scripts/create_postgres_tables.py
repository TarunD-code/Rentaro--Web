import sys
import os
import logging

# Add root folder to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_postgres_tables")

def create_tables():
    logger.info("Initializing PostgreSQL schema table structures...")
    
    try:
        # Import models to register them on their MetaData / Base
        logger.info("Importing service models to register schemas...")
        
        from auth_service import models as auth_models
        from profile_service import models as profile_models
        from property_service import models as property_models
        from payment_service import models as payment_models
        from maintenance_service import models as maintenance_models
        from onboarding_service import models as onboarding_models
        from agreements_service import models as agreements_models
        from billing_service import models as billing_models
        from owner_dashboard_service import models as dashboard_models
        from subscription_service import models as subscription_models
        from support_service import models as support_models
        from notification_service import models as notification_models
        from search_service import models as search_models
        
        # Mapping base classes
        bases = [
            ("auth", auth_models.Base),
            ("profile", profile_models.Base),
            ("property", property_models.Base),
            ("payment", payment_models.Base),
            ("maintenance", maintenance_models.Base),
            ("onboarding", onboarding_models.Base),
            ("agreements", agreements_models.Base),
            ("billing", billing_models.Base),
            ("owner_dashboard", dashboard_models.Base),
            ("subscriptions", subscription_models.Base),
            ("support", support_models.Base),
            ("notifications", notification_models.Base),
            ("search", search_models.Base),
        ]
        
        for schema_name, base in bases:
            logger.info(f"Creating tables for schema: {schema_name}...")
            # Bind the engine and create tables
            base.metadata.create_all(bind=shared_database.sync_engine)
            
        logger.info("All PostgreSQL tables successfully created!")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()
