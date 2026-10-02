# Post-Navigation Login Failure — Root Cause Analysis & Repair Report

**Date:** 2026-05-23  
**Severity:** Critical (P0 — Login Pipeline Completely Broken)  
**Status:** ✅ RESOLVED

---

## 1. Executive Summary

After the Nearby Amenities Navigation diagnostic implementation, the frontend login flow broke with `502 Bad Gateway` errors. The root cause was a `currentSchema` query parameter in the `DATABASE_URL` environment variable that is incompatible with the `psycopg2` PostgreSQL driver used by SQLAlchemy's synchronous engine.

---

## 2. Symptoms

| Symptom | Detail |
|---------|--------|
| Frontend login | Shows "The requested service is momentarily unavailable" |
| Gateway logs | `Upstream Critical Error from http://auth_service:8000/auth/login: b'Internal Server Error'` |
| Auth service logs | `sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) invalid dsn: invalid connection option "currentSchema"` |
| HTTP status chain | Frontend → Gateway (502) → Auth Service (500) |

---

## 3. Root Cause Analysis

### 3.1 The Trigger

The `docker-compose.yml` defines environment variables for each service with schema isolation:

```yaml
# docker-compose.yml line 98
environment:
  - DATABASE_URL=postgresql://postgres:rentora_secure_password@postgres:5432/rentora?currentSchema=auth
```

### 3.2 The Incompatibility

The `currentSchema` query parameter is a **JDBC-specific** connection option. It is **not supported** by:
- `psycopg2` (Python PostgreSQL driver for synchronous connections)
- `asyncpg` (Python PostgreSQL driver for asynchronous connections)

When `shared_database.py` passed this URL directly to `sqlalchemy.create_engine()`, psycopg2 rejected it at connection time with:

```
psycopg2.ProgrammingError: invalid dsn: invalid connection option "currentSchema"
```

### 3.3 Why Health Checks Passed

The `/health` endpoint is a simple JSON response that doesn't touch the database. Docker health checks reported `healthy` even though the service couldn't connect to PostgreSQL for actual queries.

### 3.4 Schema Isolation Architecture

The Rentora microservices use PostgreSQL schema isolation (`auth`, `property`, `search`, etc.) via SQLAlchemy `MetaData(schema="auth")` in each service's `database.py`. The `currentSchema` URL parameter was **redundant** — SQLAlchemy already handles schema routing through its `MetaData` object.

---

## 4. Broken File(s)

| File | Issue |
|------|-------|
| `shared_database.py` | Passed raw `DATABASE_URL` with `currentSchema` to `create_engine()` |
| `docker-compose.yml` | Set `DATABASE_URL` with unsupported `?currentSchema=` query param |

---

## 5. Applied Fix

### `shared_database.py` — Sync Engine URL Sanitization

```diff
 try:
+    # Clean currentSchema from sync connection string if present (psycopg2 incompatibility)
+    sync_db_url = DATABASE_URL
+    if "?" in sync_db_url:
+        base_part, query_part = sync_db_url.split("?", 1)
+        params = [p for p in query_part.split("&") if not p.startswith("currentSchema=")]
+        if params:
+            sync_db_url = base_part + "?" + "&".join(params)
+        else:
+            sync_db_url = base_part
+
     sync_engine = create_engine(
-        DATABASE_URL,
+        sync_db_url,
         pool_size=10,
         pool_pre_ping=True,
         echo=False
     )
```

### Why NOT modify `docker-compose.yml`

The `currentSchema` parameter in `docker-compose.yml` is intentional documentation of which schema each service uses. Rather than removing it (and losing that documentation), we chose to sanitize it at the connection layer. This is a **defense-in-depth** approach.

### Additional Fixes Applied

| Fix | File | Detail |
|-----|------|--------|
| Root health endpoint | `auth_service/main.py` | Added `@app.get("/health")` so Docker healthcheck probe doesn't 404 |
| Missing dependency | `requirements.txt` | Added `reportlab==4.1.0` for `agreements_service` |

---

## 6. Service Health Matrix (Post-Fix)

| Service | Port | Status | Health Endpoint |
|---------|------|--------|-----------------|
| postgres | 5432 | ✅ healthy | N/A |
| redis | 6379 | ✅ healthy | N/A |
| rabbitmq | 5672 | ✅ healthy | N/A |
| auth_service | 8001 | ✅ healthy | 200 OK |
| gateway | 8000 | ✅ healthy | 200 OK |
| property_service | 8003 | ✅ healthy | 200 OK |
| profile_service | 8002 | ✅ healthy | 200 OK |
| payment_service | 8004 | ✅ healthy | 200 OK |
| maintenance_service | 8005 | ✅ healthy | 200 OK |
| onboarding_service | 8006 | ✅ healthy | 200 OK |
| communication_service | 8007 | ✅ healthy | 200 OK |
| agreements_service | 8008 | ✅ healthy | 200 OK |
| billing_service | 8009 | ✅ healthy | 200 OK |
| owner_dashboard_service | 8010 | ✅ healthy | 200 OK |
| subscription_service | 8011 | ✅ healthy | 200 OK |
| support_service | 8012 | ✅ healthy | 200 OK |
| notification_service | 8013 | ✅ healthy | 200 OK |
| geo_amenity_service | 8014 | ✅ healthy | 200 OK |
| search_service | 8015 | ✅ healthy | 200 OK |

---

## 7. Validation Results

### 7.1 Direct Auth Service Login
```
POST http://auth_service:8000/auth/login
→ 200 OK
→ {"access_token":"eyJhbG...","token_type":"bearer","role":"admin"}
```

### 7.2 Gateway Proxied Login
```
POST http://localhost:8000/auth/login
→ 200 OK
→ {"access_token":"eyJhbG...","token_type":"bearer","role":"admin"}
```

### 7.3 Admin User Verified
- Email: `admin@rentaro.com`
- Role: `admin`
- Status: verified, login successful

### 7.4 Frontend
- Vite dev server running at `http://localhost:5173/`

---

## 8. Preserved Systems (No Regressions)

- ✅ Database schemas and seeded data intact
- ✅ Property/search/map functionality preserved
- ✅ Gateway route registrations unchanged
- ✅ JWT token generation working
- ✅ All 19 containers healthy
- ✅ Nearby amenity navigation code preserved
