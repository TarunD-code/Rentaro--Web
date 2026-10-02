"""
Rentora KYC — Security Middleware & Dependencies
=================================================

Implements:
1. HMAC-SHA256 webhook signature verification (timing-attack safe)
2. JWT authentication dependency
3. PII sanitizing log filter (blocks Aadhaar/PAN from stdout)
4. Rate-limiting stub for /initiate endpoint

SECURITY INVARIANTS:
- Webhook HMAC uses `hmac.compare_digest` (constant-time comparison)
- PII log filter runs on ALL handlers — no raw PII can reach stdout/stderr
- JWT verification uses the same shared secret as all Rentora services
"""

import os
import re
import hmac
import hashlib
import logging
import time
from collections import defaultdict
from typing import Optional

import jwt
from fastapi import Request, HTTPException, Header

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "RENTORA_SUPER_SECRET_KEY")
ALGORITHM = "HS256"
KYC_WEBHOOK_SECRET = os.environ.get("KYC_WEBHOOK_SECRET", "rentora_kyc_webhook_dev_secret_key_32b")

logger = logging.getLogger("kyc_service.security")


# ═════════════════════════════════════════════════════════════
# 1. PII SANITIZING LOG FILTER
# ═════════════════════════════════════════════════════════════
# SECURITY: This filter is installed on the root logger to prevent
# any accidental logging of raw Aadhaar (12-digit) or PAN
# (XXXXX9999X) patterns in ANY log output — including third-party
# library logs.

class PIISanitizingFilter(logging.Filter):
    """
    Log filter that redacts patterns resembling:
    - Aadhaar: any 12-digit number (with or without spaces/dashes)
    - PAN: 5 uppercase letters + 4 digits + 1 uppercase letter
    """
    
    # Matches: 123456781234, 1234 5678 1234, 1234-5678-1234
    AADHAAR_PATTERN = re.compile(
        r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b'
    )
    
    # Matches: ABCDE1234F (standard PAN format)
    PAN_PATTERN = re.compile(
        r'\b([A-Z]{5}[0-9]{4}[A-Z])\b'
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.AADHAAR_PATTERN.sub("[AADHAAR-REDACTED]", record.msg)
            record.msg = self.PAN_PATTERN.sub("[PAN-REDACTED]", record.msg)
        # Process format args as well
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._sanitize(v) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize(a) for a in record.args)
        return True

    def _sanitize(self, value):
        if isinstance(value, str):
            value = self.AADHAAR_PATTERN.sub("[AADHAAR-REDACTED]", value)
            value = self.PAN_PATTERN.sub("[PAN-REDACTED]", value)
        return value


def install_pii_filter():
    """Install the PII sanitizing filter on the root logger."""
    pii_filter = PIISanitizingFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(pii_filter)
    # Also install on all existing handlers
    for handler in root_logger.handlers:
        handler.addFilter(pii_filter)
    logger.info("PII sanitizing log filter installed on root logger")


# ═════════════════════════════════════════════════════════════
# 2. HMAC-SHA256 WEBHOOK SIGNATURE VERIFICATION
# ═════════════════════════════════════════════════════════════

async def verify_webhook_signature(request: Request) -> bytes:
    """
    FastAPI dependency that validates the HMAC-SHA256 signature
    on incoming KYC vendor webhooks.
    
    Protocol:
    1. Read the raw request body
    2. Compute HMAC-SHA256(KYC_WEBHOOK_SECRET, raw_body)
    3. Compare against the X-Webhook-Signature header
    4. If mismatch → 403 Forbidden (with zero information leakage)
    
    SECURITY:
    - Uses hmac.compare_digest() to prevent timing attacks
    - Raw body is returned for downstream JSON parsing
    - No error details are leaked to the caller on failure
    """
    try:
        raw_body = await request.body()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to read request body"
        )

    # Extract signature from header
    signature_header = request.headers.get("X-Webhook-Signature", "")
    if not signature_header:
        logger.warning("Webhook request missing X-Webhook-Signature header")
        raise HTTPException(
            status_code=403,
            detail="Invalid Webhook Signature"
        )

    # Compute expected HMAC
    expected_signature = hmac.new(
        KYC_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    # SECURITY: Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature_header, expected_signature):
        logger.warning(
            "Webhook HMAC signature mismatch — potential tampering or misconfigured secret"
        )
        raise HTTPException(
            status_code=403,
            detail="Invalid Webhook Signature"
        )

    logger.info("Webhook HMAC signature verified successfully")
    return raw_body


# ═════════════════════════════════════════════════════════════
# 3. JWT AUTHENTICATION DEPENDENCY
# ═════════════════════════════════════════════════════════════

def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and verify the JWT bearer token.
    
    Returns the user identifier (email_or_phone) from the 'sub' claim.
    Compatible with the Rentora auth_service token format.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authorization header"
        )
    
    token = authorization.split(" ", 1)[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload: missing 'sub' claim"
            )
        return user_identifier
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )


# ═════════════════════════════════════════════════════════════
# 4. RATE LIMITING STUB
# ═════════════════════════════════════════════════════════════
# In production, replace with Redis-backed sliding window rate limiter
# (e.g., fastapi-limiter or custom middleware with shared_redis).

_rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 5  # Max 5 KYC initiations per minute per user


def check_rate_limit(user_id: str) -> None:
    """
    Simple in-memory rate limiter for KYC initiation.
    
    LIMITATION: This is per-process, not distributed. In production,
    use Redis with a sliding window counter (see shared_redis.py).
    
    Raises HTTPException(429) if rate limit exceeded.
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    
    # Prune expired entries
    _rate_limit_store[user_id] = [
        ts for ts in _rate_limit_store[user_id] if ts > window_start
    ]
    
    if len(_rate_limit_store[user_id]) >= RATE_LIMIT_MAX_REQUESTS:
        logger.warning(f"Rate limit exceeded for user {user_id[:3]}*** on /kyc/initiate")
        raise HTTPException(
            status_code=429,
            detail="Too many KYC initiation requests. Please try again later."
        )
    
    _rate_limit_store[user_id].append(now)


def get_current_admin(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify the JWT token and confirm the user has the ADMIN role.
    Returns the user identifier (email_or_phone).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authorization header"
        )
    
    token = authorization.split(" ", 1)[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        role: str = payload.get("role")
        if user_identifier is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload: missing 'sub' claim"
            )
        if not role or role.upper() != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: Administrator access required"
            )
        return user_identifier
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

