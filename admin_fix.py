from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth_service.models import User, Base
from passlib.context import CryptContext

# Use the same DB URL as in database.py
SQLALCHEMY_DATABASE_URL = "sqlite:///./rentora_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def ensure_admin():
    db = SessionLocal()
    email = "admin@rentora.com"
    admin = db.query(User).filter(User.email_or_phone == email).first()
    
    if admin:
        print(f"User {email} already exists. Updating to Admin role...")
        admin.role = "admin"
        admin.is_verified = True
        db.commit()
    else:
        print(f"Creating Admin user: {email}")
        hashed_pwd = pwd_context.hash("admin123")
        new_admin = User(
            email_or_phone=email,
            hashed_password=hashed_pwd,
            role="admin",
            is_verified=True
        )
        db.add(new_admin)
        db.commit()
    print("Admin verification complete.")
    db.close()

if __name__ == "__main__":
    ensure_admin()
