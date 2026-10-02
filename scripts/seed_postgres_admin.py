import sys
import os
import logging
import bcrypt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database
from auth_service import models as auth_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_admin")

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_admin():
    if not shared_database.SyncSessionLocal:
        logger.error("SyncSessionLocal not initialized")
        return

    logger.info("Connecting to PostgreSQL to seed admin user...")
    db = shared_database.SyncSessionLocal()
    
    try:
        email = "admin@rentaro.com"
        password = "admin123"
        role = "admin"
        
        # Check if exists
        user = db.query(auth_models.User).filter(auth_models.User.email_or_phone == email).first()
        if user:
            logger.info(f"Admin user {email} already exists. Updating password and role...")
            user.hashed_password = get_password_hash(password)
            user.role = role
            user.is_verified = True
        else:
            logger.info(f"Creating new admin user {email}...")
            user = auth_models.User(
                email_or_phone=email,
                hashed_password=get_password_hash(password),
                role=role,
                is_verified=True,
                otp_code=None
            )
            db.add(user)
            
        db.commit()
        logger.info(f"✅ Admin user {email} successfully seeded with password: {password}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
