import logging
import datetime
import uuid
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from .rate_limiter import check_rate_limit
import shared_redis
import shared_database
import shared_storage
import shared_event_broker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="Rentora API Gateway")

# Correlation ID and request logging middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    logger.info(f"[{correlation_id}] → {request.method} {request.url.path}")
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

import os as _os

_IS_PROD = _os.environ.get("ENV", "").lower() == "production"
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Correlation-ID"],
)


# ── Security headers — applied to every response leaving the gateway ─────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]      = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "   # React inline scripts
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.olamaps.io https://api.maptiler.com; "
        "frame-ancestors 'none';"
    )
    if _IS_PROD:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

app.mount("/static", StaticFiles(directory="uploads"), name="static")


import os

is_production = os.environ.get("ENV") == "production"

if is_production:
    AUTH_SERVICE_URL = "http://auth_service:8000"
    PROFILE_SERVICE_URL = "http://profile_service:8000"
    PROPERTY_SERVICE_URL = "http://property_service:8000"
    PAYMENT_SERVICE_URL = "http://payment_service:8000"
    MAINTENANCE_SERVICE_URL = "http://maintenance_service:8000"
    ONBOARDING_SERVICE_URL = "http://onboarding_service:8000"
    COMMUNICATION_SERVICE_URL = "http://communication_service:8007"
    BILLING_SERVICE_URL = "http://billing_service:8000"
    OWNER_DASHBOARD_SERVICE_URL = "http://owner_dashboard_service:8000"
    SUBSCRIPTION_SERVICE_URL = "http://subscription_service:8000"
    SUPPORT_SERVICE_URL = "http://support_service:8000"
    AGREEMENTS_SERVICE_URL = "http://agreements_service:8000"
    NOTIFICATION_SERVICE_URL = "http://notification_service:8000"
    GEO_AMENITY_SERVICE_URL = "http://geo_amenity_service:8000"
    SEARCH_SERVICE_URL = "http://search_service:8000"
    KYC_SERVICE_URL = "http://kyc_service:8000"
else:
    AUTH_SERVICE_URL = "http://127.0.0.1:8001"
    PROFILE_SERVICE_URL = "http://127.0.0.1:8002"
    PROPERTY_SERVICE_URL = "http://127.0.0.1:8003"
    PAYMENT_SERVICE_URL = "http://127.0.0.1:8004"
    MAINTENANCE_SERVICE_URL = "http://127.0.0.1:8005"
    ONBOARDING_SERVICE_URL = "http://127.0.0.1:8006"
    COMMUNICATION_SERVICE_URL = "http://127.0.0.1:8007"
    AGREEMENTS_SERVICE_URL = "http://127.0.0.1:8008"
    BILLING_SERVICE_URL = "http://127.0.0.1:8009"
    OWNER_DASHBOARD_SERVICE_URL = "http://127.0.0.1:8010"
    SUBSCRIPTION_SERVICE_URL = "http://127.0.0.1:8011"
    SUPPORT_SERVICE_URL = "http://127.0.0.1:8012"
    NOTIFICATION_SERVICE_URL = "http://127.0.0.1:8013"
    GEO_AMENITY_SERVICE_URL = "http://127.0.0.1:8014"
    SEARCH_SERVICE_URL = "http://127.0.0.1:8015"
    KYC_SERVICE_URL = "http://127.0.0.1:8016"

# Reusable async HTTP client (avoids connection leak)
http_client = httpx.AsyncClient(timeout=60.0)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

async def reverse_proxy(request: Request, upstream_url: str, prefix_to_strip: str = None):
    """Forward the request to the upstream service, optionally stripping a prefix."""
    path = request.url.path
    if prefix_to_strip:
        # Strip the service prefix: /profile/me → /me
        path = path[len(f"/{prefix_to_strip}"):]
        if not path:
            path = "/"

    url = f"{upstream_url}{path}"
    query_string = str(request.query_params)
    if query_string:
        url = f"{url}?{query_string}"

    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Forward the correlation ID downstream to microservices
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    headers["X-Correlation-ID"] = correlation_id
    
    body = await request.body()

    logger.info(f"[{correlation_id}] → {request.method} {request.url.path} => {url}")


    try:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        
        resp_headers = dict(response.headers)
        resp_headers.pop("transfer-encoding", None)
        resp_headers.pop("content-length", None)
        
        # Consistent CORS handling at the Gateway level
        # Only reflect origins that are in our allow-list
        origin = request.headers.get("origin", "")
        allowed_origin = origin if origin in _ALLOWED_ORIGINS else _ALLOWED_ORIGINS[0]
        resp_headers["Access-Control-Allow-Origin"]      = allowed_origin
        resp_headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        resp_headers["Access-Control-Allow-Headers"]     = "Authorization, Content-Type, Accept"
        resp_headers["Access-Control-Allow-Credentials"] = "true"

        if response.status_code >= 500:
            logger.error(f"Upstream Critical Error from {url}: {response.content}")
            return StreamingResponse(
                iter([b'{"detail": "The requested service is momentarily unavailable. Please try again in a few seconds."}']),
                status_code=502,
                headers={"Content-Type": "application/json", **resp_headers}
            )

        logger.info(f"← {response.status_code} from {url}")
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=resp_headers,
        )
    except httpx.RequestError as exc:
        logger.error(f"✗ Network failure connecting to {upstream_url}: {exc}")
        return StreamingResponse(
            iter([b'{"detail": "System connectivity issue. Please ensure all backend services are running and try again."}']),
            status_code=503,
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": _ALLOWED_ORIGINS[0],
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
            }
        )


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        return StreamingResponse(
            iter([b'{"detail": "Too many requests. Please slow down."}']),
            status_code=429,
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": request.headers.get("origin", _ALLOWED_ORIGINS[0]),
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    return await call_next(request)

@app.get("/diagnostics")
async def get_diagnostics():
    services = {
        "auth_service": (AUTH_SERVICE_URL, 8001),
        "profile_service": (PROFILE_SERVICE_URL, 8002),
        "property_service": (PROPERTY_SERVICE_URL, 8003),
        "payment_service": (PAYMENT_SERVICE_URL, 8004),
        "maintenance_service": (MAINTENANCE_SERVICE_URL, 8005),
        "onboarding_service": (ONBOARDING_SERVICE_URL, 8006),
        "communication_service": (COMMUNICATION_SERVICE_URL, 8007),
        "agreements_service": (AGREEMENTS_SERVICE_URL, 8008),
        "billing_service": (BILLING_SERVICE_URL, 8009),
        "owner_dashboard_service": (OWNER_DASHBOARD_SERVICE_URL, 8010),
        "subscription_service": (SUBSCRIPTION_SERVICE_URL, 8011),
        "support_service": (SUPPORT_SERVICE_URL, 8012),
        "notification_service": (NOTIFICATION_SERVICE_URL, 8013),
        "geo_amenity_service": (GEO_AMENITY_SERVICE_URL, 8014),
        "search_service": (SEARCH_SERVICE_URL, 8015),
        "kyc_service": (KYC_SERVICE_URL, 8016),
    }
    
    diagnostic_report = {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "gateway": {
            "status": "healthy",
            "jwt_secret_configured": True
        },
        "infrastructure": {},
        "services": {}
    }
    
    # 1. Probe PostgreSQL Status
    try:
        from shared_database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        diagnostic_report["infrastructure"]["postgres"] = "online"
    except Exception as e:
        diagnostic_report["infrastructure"]["postgres"] = f"offline ({e})"
        diagnostic_report["status"] = "degraded"
        
    # 2. Probe Redis Caching Status
    try:
        client = shared_redis._get_redis_client()
        if client and client.ping():
            diagnostic_report["infrastructure"]["redis"] = "online"
        else:
            diagnostic_report["infrastructure"]["redis"] = "offline"
            diagnostic_report["status"] = "degraded"
    except Exception as e:
        diagnostic_report["infrastructure"]["redis"] = f"offline ({e})"
        diagnostic_report["status"] = "degraded"
        
    # 3. Probe RabbitMQ Message Broker Status
    try:
        conn, ch = shared_event_broker._get_connection_and_channel()
        if conn and conn.is_open:
            diagnostic_report["infrastructure"]["rabbitmq"] = "online"
        else:
            diagnostic_report["infrastructure"]["rabbitmq"] = "offline"
            diagnostic_report["status"] = "degraded"
    except Exception as e:
        diagnostic_report["infrastructure"]["rabbitmq"] = f"offline ({e})"
        diagnostic_report["status"] = "degraded"
        
    # 4. Probe Object Storage Status
    try:
        provider = shared_storage.STORAGE_PROVIDER
        client = shared_storage._get_s3_client()
        diagnostic_report["infrastructure"]["storage"] = {
            "provider": provider,
            "status": "online" if (provider == "local" or client is not None) else "degraded"
        }
    except Exception as e:
        diagnostic_report["infrastructure"]["storage"] = {
            "status": f"offline ({e})"
        }
        diagnostic_report["status"] = "degraded"
    
    async def check_service(name: str, url: str, port: int):
        health_url = f"{url}/auth/health" if name == "auth_service" else f"{url}/health"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(health_url)
                if res.status_code == 200:
                    return name, {
                        "status": "online",
                        "port": port,
                        "health_endpoint": res.json()
                    }
                else:
                    return name, {
                        "status": "unhealthy",
                        "port": port,
                        "error": f"HTTP {res.status_code}"
                    }
        except Exception as e:
            return name, {
                "status": "offline",
                "port": port,
                "error": str(e)
            }
            
    import asyncio
    tasks = [check_service(n, u, p) for n, (u, p) in services.items()]
    results = await asyncio.gather(*tasks)
    
    for name, report in results:
        diagnostic_report["services"][name] = report
        if report["status"] != "online":
            diagnostic_report["status"] = "degraded"
            
    return diagnostic_report


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def gateway_router(request: Request, path: str):
    # Handle CORS Preflight (OPTIONS) directly at the gateway for all routes
    if request.method == "OPTIONS":
        origin = request.headers.get("origin")
        headers = {
            "Access-Control-Allow-Origin": origin if origin else "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        }
        return Response(status_code=204, headers=headers)

    if path.startswith("auth"):
        # Auth service now uses /auth prefix internally, so don't strip
        return await reverse_proxy(request, AUTH_SERVICE_URL, prefix_to_strip=None)
    elif path.startswith("profile/notifications"):
        # Map profile/notifications to the standalone service's /history endpoint
        return await reverse_proxy(request, NOTIFICATION_SERVICE_URL, prefix_to_strip="profile/notifications")
    elif path.startswith("profile"):
        return await reverse_proxy(request, PROFILE_SERVICE_URL, prefix_to_strip="profile")
    elif path.startswith("property/agreements"):
        # Route property/agreements to property_service which has the full agreement system
        # (generate, sign, download). Strip only "property" prefix so /agreements/... is forwarded.
        return await reverse_proxy(request, PROPERTY_SERVICE_URL, prefix_to_strip="property")
    elif path.startswith("property"):
        return await reverse_proxy(request, PROPERTY_SERVICE_URL, prefix_to_strip="property")
    elif path.startswith("payment"):
        return await reverse_proxy(request, PAYMENT_SERVICE_URL, prefix_to_strip="payment")
    elif path.startswith("maintenance"):
        return await reverse_proxy(request, MAINTENANCE_SERVICE_URL, prefix_to_strip="maintenance")
    elif path.startswith("onboarding"):
        return await reverse_proxy(request, ONBOARDING_SERVICE_URL, prefix_to_strip="onboarding")
    elif path.startswith("communication"):
        return await reverse_proxy(request, COMMUNICATION_SERVICE_URL, prefix_to_strip="communication")
    elif path.startswith("billing"):
        return await reverse_proxy(request, BILLING_SERVICE_URL, prefix_to_strip="billing")
    elif path.startswith("owner-dashboard"):
        return await reverse_proxy(request, OWNER_DASHBOARD_SERVICE_URL, prefix_to_strip="owner-dashboard")
    elif path.startswith("subscriptions"):
        return await reverse_proxy(request, SUBSCRIPTION_SERVICE_URL, prefix_to_strip="subscriptions")
    elif path.startswith("support"):
        return await reverse_proxy(request, SUPPORT_SERVICE_URL, prefix_to_strip="support")
    elif path.startswith("agreements"):
        return await reverse_proxy(request, AGREEMENTS_SERVICE_URL, prefix_to_strip="agreements")
    elif path.startswith("notifications"):
        return await reverse_proxy(request, NOTIFICATION_SERVICE_URL, prefix_to_strip="notifications")
    elif path.startswith("geo"):
        return await reverse_proxy(request, GEO_AMENITY_SERVICE_URL, prefix_to_strip="geo")
    elif path.startswith("search"):
        return await reverse_proxy(request, SEARCH_SERVICE_URL, prefix_to_strip=None)
    elif path.startswith("recommendations"):
        return await reverse_proxy(request, SEARCH_SERVICE_URL, prefix_to_strip=None)
    elif path.startswith("kyc"):
        return await reverse_proxy(request, KYC_SERVICE_URL, prefix_to_strip="kyc")
    
    return StreamingResponse(
        iter([b'{"detail": "Route not found"}']),
        status_code=404,
        headers={"Content-Type": "application/json"}
    )
