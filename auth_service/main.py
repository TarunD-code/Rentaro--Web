import os
from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, Depends, HTTPException, Request, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas, database, otp_providers

# Secret key for JWTs — loaded from environment, falls back to stable dev default.
# Must match JWT_SECRET_KEY in .env and shared_database.JWT_SECRET_KEY.
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "RENTORA_SUPER_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

import bcrypt
import logging
import sys
import os as _os

# Path so shared_rate_limiter is importable inside Docker
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from shared_rate_limiter import rate_limit

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_service")

# ── Allowed origins — never wildcard in production ────────────────────────────
_IS_PROD = os.environ.get("ENV", "").lower() == "production"
_ALLOWED_ORIGINS = (
    [
        "https://rentora.in",
        "https://www.rentora.in",
        "https://app.rentora.in",
    ]
    if _IS_PROD
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.5:5173",
    ]
)

# App Setup
app = FastAPI(title="Rentora Auth Service")
auth_router = APIRouter(prefix="/auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Security headers middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]      = "geolocation=(), microphone=(), camera=()"
    if _IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

def get_password_hash(password):
    # Direct bcrypt to avoid passlib Python 3.13 issues
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    # Direct bcrypt verification
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/health")
def root_health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@auth_router.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@auth_router.post("/signup", response_model=schemas.UserOut)
def create_user(
    request: Request,
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    _rl: None = Depends(rate_limit(
        "signup", max_calls=3, window_seconds=300,   # 3 per 5 min per IP
        detail="Too many signup attempts. Please wait 5 minutes.",
    )),
):
    # Defence-in-depth: reject admin self-assignment even if the Pydantic validator
    # is somehow bypassed (e.g. direct service call bypassing the gateway).
    if user.role.strip().lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be created via public registration. "
                   "Contact your system administrator.",
        )

    db_user = db.query(models.User).filter(models.User.email_or_phone == user.email_or_phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Identifier already registered")
    
    hashed_pwd = get_password_hash(user.password)
    # Generate and Send OTP
    otp_code = otp_providers.generate_otp()
    
    new_user = models.User(
        email_or_phone=user.email_or_phone,
        hashed_password=hashed_pwd,
        role=user.role,
        is_verified=False,
        otp_code=otp_code
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User saved to DB: {new_user.email_or_phone[:3]}***")
    
    otp_providers.send_otp(user.email_or_phone, otp_code)
    
    return new_user

@auth_router.post("/verify-otp")
def verify_otp(
    request: Request,
    otp_data: schemas.OTPVerify,
    db: Session = Depends(database.get_db),
    _rl: None = Depends(rate_limit(
        "verify_otp", max_calls=3, window_seconds=300,  # 3 per 5 min per IP
        detail="Too many OTP attempts. Please wait 5 minutes.",
    )),
):
    db_user = db.query(models.User).filter(models.User.email_or_phone == otp_data.email_or_phone).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # DEV_MODE bypass: "000000" is accepted as a universal code in non-production.
    import os
    dev_mode = os.environ.get("DEV_MODE", "true").lower() in ("true", "1", "yes")
    is_bypass = dev_mode and otp_data.otp == "000000"

    if not is_bypass and (not db_user.otp_code or db_user.otp_code != otp_data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    db_user.is_verified = True
    db_user.otp_code = None # Clear OTP after verification
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email_or_phone, "role": db_user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": db_user.role}

@auth_router.post("/login")
def login(
    request: Request,
    user_creds: schemas.UserLogin,
    db: Session = Depends(database.get_db),
    _rl: None = Depends(rate_limit(
        "login", max_calls=5, window_seconds=60,   # 5 per minute per IP
        detail="Too many login attempts. Please wait 1 minute.",
    )),
):
    # 1. Fetch user and verify credentials
    logger.info(f"Login attempt received for: {user_creds.email_or_phone[:3]}***")
    db_user = db.query(models.User).filter(models.User.email_or_phone == user_creds.email_or_phone).first()
    
    if not db_user:
        logger.warning(f"Login failed: User {user_creds.email_or_phone[:3]}*** not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )
    
    try:
        is_valid = verify_password(user_creds.password, db_user.hashed_password)
        if not is_valid:
            logger.warning(f"Login failed: Password mismatch for user {user_creds.email_or_phone[:3]}***")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
    except HTTPException:
        # Re-raise HTTP exceptions to avoid them being caught by the generic handler
        raise
    except Exception as e:
        logger.error(f"Internal error during password verification for {user_creds.email_or_phone}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An internal authentication error occurred. Please contact support."
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
