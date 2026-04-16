import logging
from fastapi import FastAPI, Request, HTTPException, Response
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

AUTH_SERVICE_URL = "http://127.0.0.1:8001"
PROFILE_SERVICE_URL = "http://127.0.0.1:8002"
PROPERTY_SERVICE_URL = "http://127.0.0.1:8003"
PAYMENT_SERVICE_URL = "http://127.0.0.1:8004"
MAINTENANCE_SERVICE_URL = "http://127.0.0.1:8005"
ONBOARDING_SERVICE_URL = "http://127.0.0.1:8006"
COMMUNICATION_SERVICE_URL = "http://127.0.0.1:8007"

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
        resp_headers.pop("content-length", None)

        origin = request.headers.get("origin", "*")
        resp_headers["Access-Control-Allow-Origin"] = origin
        resp_headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        resp_headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
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
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
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
    elif path.startswith("profile"):
        return await reverse_proxy(request, PROFILE_SERVICE_URL, prefix_to_strip="profile")
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
    
    return StreamingResponse(
        iter([b'{"detail": "Route not found"}']),
        status_code=404,
        headers={"Content-Type": "application/json"}
    )
