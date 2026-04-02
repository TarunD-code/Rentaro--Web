from profile_service import models, database

def cleanup_kyc():
    db = next(database.get_db())
    # Inconsistent rows: status = 'pending' but no documents
    profiles = db.query(models.UserProfile).filter(models.UserProfile.kyc_status == 'pending').all()
    
    updated_count = 0
    for profile in profiles:
        docs = db.query(models.KYCDocument).filter(models.KYCDocument.profile_id == profile.id).all()
        if not docs:
            print(f"Fixing profile {profile.user_identifier}: status changed from pending to not_submitted")
            profile.kyc_status = 'not_submitted'
            updated_count += 1
    
    db.commit()
    print(f"Cleanup complete. Updated {updated_count} profiles.")

if __name__ == "__main__":
    cleanup_kyc()
