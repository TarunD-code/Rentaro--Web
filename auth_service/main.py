from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas, database, otp_providers

# Secret key for JWTs and PyJWT setup
SECRET_KEY = "RENTORA_SUPER_SECRET_KEY"  # In production, use environs!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Mock Redis Store for OTPs (In-memory fallback)
OTP_STORE = {}

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# App Setup
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Rentora Auth Service")
auth_router = APIRouter(prefix="/auth")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@auth_router.post("/signup", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email_or_phone == user.email_or_phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Identifier already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(
        email_or_phone=user.email_or_phone,
        hashed_password=hashed_pwd,
        role=user.role,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate and Send OTP
    otp_code = otp_providers.generate_otp()
    OTP_STORE[user.email_or_phone] = otp_code
    otp_providers.send_otp(user.email_or_phone, otp_code)
    
    return new_user

@auth_router.post("/verify-otp")
def verify_otp(otp_data: schemas.OTPVerify, db: Session = Depends(database.get_db)):
    stored_otp = OTP_STORE.get(otp_data.email_or_phone)
    if not stored_otp or stored_otp != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    db_user = db.query(models.User).filter(models.User.email_or_phone == otp_data.email_or_phone).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_user.is_verified = True
    db.commit()
    
    # Clear OTP
    del OTP_STORE[otp_data.email_or_phone]
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email_or_phone, "role": db_user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": db_user.role}

@auth_router.post("/login")
def login(user_creds: schemas.UserLogin, db: Session = Depends(database.get_db)):
    # Fetch user from DB
    db_user = db.query(models.User).filter(models.User.email_or_phone == user_creds.email_or_phone).first()
    
    # 1. Check if user exists & password is correct
    if not db_user or not verify_password(user_creds.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )
        
    # 2. Check if verified
    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User is not verified"
        )
        
    # 3. Generate Token (Always use role from DB for security)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email_or_phone, "role": db_user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": db_user.role}

app.include_router(auth_router)
