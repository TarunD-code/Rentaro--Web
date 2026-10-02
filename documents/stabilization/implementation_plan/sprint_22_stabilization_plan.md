# Platform Stabilization & Runtime Recovery Sprint

This sprint addresses the critical failures preventing the Rentora microservices and API Gateway from reaching a healthy, operational state inside Docker.

## Open Questions

None. The issues have been fully diagnosed. The root causes are directly linked to manual `.env` file parsing overriding Docker-Compose network variables, the Gateway pointing to its own container interface, and missing backwards-compatibility exports in the shared DB module.

## Proposed Changes

---

### Shared Modules

#### [MODIFY] [shared_database.py](file:///d:/Python%20Projects/Rentaro/shared_database.py)
- **Backward Compatibility:** Export `engine = sync_engine` and `SessionLocal = SyncSessionLocal`.
- **Environment Safeties:** Change `.env` file loading to use `os.environ.setdefault()` instead of direct assignment `os.environ[]`. This ensures `docker-compose.yml` environment variables are not overwritten.
- **Docker Fallbacks:** Update `DEFAULT_DATABASE_URL` and `DEFAULT_SYNC_URL` to default to `postgres` instead of `localhost`.

#### [MODIFY] [shared_redis.py](file:///d:/Python%20Projects/Rentaro/shared_redis.py)
- **Environment Safeties:** Change `.env` file loading to use `os.environ.setdefault()`.
- **Docker Fallbacks:** Update `REDIS_URL` and `REDIS_HOST` fallbacks to default to `redis` instead of `localhost`.

#### [MODIFY] [shared_event_broker.py](file:///d:/Python%20Projects/Rentaro/shared_event_broker.py)
- **Environment Safeties:** Change `.env` file loading to use `os.environ.setdefault()`.
- **Docker Fallbacks:** Update `RABBITMQ_URL` fallback to default to `rabbitmq` instead of `localhost`.

---

### Search Intelligence

#### [MODIFY] [search_service/database.py](file:///d:/Python%20Projects/Rentaro/search_service/database.py)
- **Environment Safeties:** Change `.env` file loading to use `os.environ.setdefault()`.
- **Docker Fallbacks:** Update fallback URL to default to `postgres` instead of `localhost`.

---

### API Gateway

#### [MODIFY] [gateway/main.py](file:///d:/Python%20Projects/Rentaro/gateway/main.py)
- **Service Registry Fix:** Change all internal URLs from `http://127.0.0.1:<external_port>` to their internal Docker network DNS names and internal ports (e.g., `http://auth_service:8000`, `http://communication_service:8007`). This fixes the "All connection attempts failed" diagnostics error.
- **Route Prefix Fix:** Modify the reverse proxy rules for `search` and `recommendations` to use `prefix_to_strip=None`, preserving the full paths (e.g., `/search/properties`) as expected by `search_service/main.py`. This fixes the 404s.

---

### Walkthrough & Tooling

#### [NEW] [sprint_22_stabilization.md](file:///d:/Python%20Projects/Rentaro/documents/stabilization/walkthrough/sprint_22_stabilization.md)
- Write the final walkthrough containing the root-cause analysis report and all executed fixes.

#### [NEW] [runtime_validation.py](file:///d:/Python%20Projects/Rentaro/scripts/runtime_validation.py)
- A specialized diagnostics script that polls the API Gateway's `/diagnostics` endpoint, verifies the status of all 15 microservices and core infrastructure, and validates the HTTP endpoints for `/search/autocomplete` and `/search/properties` to produce a final readiness score.

## Verification Plan

### Automated Tests
1. Wait for Docker container rebuilds.
2. Run `python scripts/runtime_validation.py` to assert >90% production readiness.
3. Check the Gateway `/diagnostics` payload to verify all services are "online".
4. Ping the `/search/autocomplete` API to ensure 200 OK.
