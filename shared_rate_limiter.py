"""
Rentora — Shared Redis Rate Limiter
=====================================
Provides a reusable FastAPI dependency that enforces per-key sliding-window
rate limits backed by Redis.  Falls back gracefully (allows the request) when
Redis is unavailable so a cache outage never blocks normal platform traffic.

Usage in a route:
    from shared_rate_limiter import rate_limit

    @router.post("/login")
    def login(
        request: Request,
        _: None = Depends(rate_limit("login", max_calls=5, window_seconds=60)),
    ):
        ...

Key strategy:
    - For unauthenticated endpoints (login, signup, OTP) the key is the
      client IP so credential-stuffing bots can't cycle across accounts.
    - For authenticated spam-prevention endpoints (visit booking, contact)
      pass key_fn="user" to scope the window to the authenticated user.
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Depends, HTTPException, Request, status

logger = logging.getLogger("rate_limiter")

_REDIS_UNAVAILABLE_WARNED = False


def _get_redis():
    try:
        import shared_redis
        return shared_redis._get_redis_client()
    except Exception:
        return None


def rate_limit(
    bucket: str,
    max_calls: int,
    window_seconds: int,
    key_fn: str = "ip",          # "ip" | "user"
    status_code: int = 429,
    detail: str = "Too many requests. Please slow down.",
) -> Callable:
    """
    Returns a FastAPI dependency that enforces a sliding-window rate limit.

    Args:
        bucket:         Logical name for this limit (e.g. "login", "signup").
        max_calls:      Maximum number of allowed calls in the window.
        window_seconds: Length of the rolling window in seconds.
        key_fn:         "ip"   → key off client IP (good for auth endpoints).
                        "user" → key off the JWT sub claim (good for per-user
                                 spam prevention on booking/contact endpoints).
        status_code:    HTTP status returned when the limit is exceeded (429).
        detail:         Error message body.
    """

    def dependency(request: Request) -> None:
        global _REDIS_UNAVAILABLE_WARNED

        client = _get_redis()
        if client is None:
            if not _REDIS_UNAVAILABLE_WARNED:
                logger.warning(
                    "[RateLimiter] Redis unavailable — rate limiting disabled. "
                    "Set REDIS_URL in .env to enable."
                )
                _REDIS_UNAVAILABLE_WARNED = True
            return  # Fail-open: allow all requests when Redis is down

        # Build the rate-limit key
        if key_fn == "user":
            auth = request.headers.get("Authorization", "")
            subject = "anonymous"
            if auth.startswith("Bearer "):
                try:
                    import os, jwt as _jwt
                    secret = os.environ.get("JWT_SECRET_KEY", "RENTORA_SUPER_SECRET_KEY")
                    payload = _jwt.decode(auth.split(" ")[1], secret, algorithms=["HS256"])
                    subject = payload.get("sub", "anonymous")
                except Exception:
                    pass
            raw_key = subject
        else:
            # Client IP — prefer X-Forwarded-For set by the gateway
            forwarded = request.headers.get("X-Forwarded-For")
            raw_key = forwarded.split(",")[0].strip() if forwarded else (
                request.client.host if request.client else "unknown"
            )

        redis_key = f"rl:{bucket}:{raw_key}"

        try:
            now_ms  = int(time.time() * 1000)
            cutoff  = now_ms - (window_seconds * 1000)

            pipe = client.pipeline()
            # Remove timestamps outside the window
            pipe.zremrangebyscore(redis_key, "-inf", cutoff)
            # Count remaining timestamps
            pipe.zcard(redis_key)
            # Add this request's timestamp
            pipe.zadd(redis_key, {str(now_ms): now_ms})
            # Reset TTL so the key auto-expires after inactivity
            pipe.expire(redis_key, window_seconds * 2)
            results = pipe.execute()

            current_count = results[1]   # zcard result (before adding current)

            if current_count >= max_calls:
                retry_after = window_seconds
                raise HTTPException(
                    status_code=status_code,
                    detail=detail,
                    headers={"Retry-After": str(retry_after)},
                )

        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"[RateLimiter] Redis error for key '{redis_key}': {exc} — allowing request.")

    return dependency
