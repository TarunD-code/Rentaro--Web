import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from .rate_limiter import check_rate_limit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="Rentora API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
PROFILE_SERVICE_URL = "http://127.0.0.1:8002"
PROPERTY_SERVICE_URL = "http://127.0.0.1:8003"

# Reusable async HTTP client (avoids connection leak)
http_client = httpx.AsyncClient(timeout=10.0)

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
    body = await request.body()

    logger.info(f"→ {request.method} {request.url.path} => {url}")

    try:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        
        resp_headers = dict(response.headers)
        resp_headers.pop("transfer-encoding", None)
        resp_headers.pop("content-length", None) # Let StreamingResponse handle it

        logger.info(f"← {response.status_code} from {url}")

        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=resp_headers,
        )
    except httpx.RequestError as exc:
        logger.error(f"✗ Upstream unreachable: {upstream_url} — {exc}")
        return StreamingResponse(
            iter([b'{"detail": "Upstream service unavailable or timed out"}']),
            status_code=502,
            headers={"Content-Type": "application/json"}
        )

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        return StreamingResponse(
            iter([b'{"detail": "Too many requests. Please slow down."}']),
            status_code=429,
            headers={"Content-Type": "application/json"}
        )
    return await call_next(request)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def gateway_router(request: Request, path: str):
    if path.startswith("auth"):
        # Auth service now uses /auth prefix internally, so don't strip
        return await reverse_proxy(request, AUTH_SERVICE_URL, prefix_to_strip=None)
    elif path.startswith("profile"):
        return await reverse_proxy(request, PROFILE_SERVICE_URL, prefix_to_strip="profile")
    elif path.startswith("property"):
        return await reverse_proxy(request, PROPERTY_SERVICE_URL, prefix_to_strip="property")
    
    return StreamingResponse(
        iter([b'{"detail": "Route not found"}']),
        status_code=404,
        headers={"Content-Type": "application/json"}
    )
