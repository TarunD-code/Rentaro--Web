import sys
import os
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from payment_service.database import engine
from payment_service import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sprint14_migration")

def run_migration():
    logger.info("Starting Sprint 14 Migration: Owner Payouts, Ledger, and Accounting")
    
    logger.info("Creating new tables...")
    try:
        # metadata.create_all is safe, it will only create tables that do not exist yet.
        models.Base.metadata.create_all(bind=engine)
        logger.info("Successfully created OwnerBalance, LedgerEntry, FeeRecord, TaxRecord, and Payout tables.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
