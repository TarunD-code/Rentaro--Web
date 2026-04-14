"""
Sprint 13 DB Migration Script

Creates the rentora_onboarding.db tables for:
- OnboardingRecord
- OnboardingKYC 
- DigitalAgreement
- SignatureRecord
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onboarding_service.database import engine
from onboarding_service import models

def migrate():
    print("Running Sprint 13 migrations for Onboarding Service...")
    models.Base.metadata.create_all(bind=engine)
    print("[OK] All tables created successfully.")

if __name__ == "__main__":
    migrate()
