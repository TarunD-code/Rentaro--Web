# Listings & Search Recovery Report

**Date:** 2026-05-23  
**Status:** ✅ RESOLVED  
**Impact:** Critical (P0 — Browse Listings showing zero properties)

---

## 1. Executive Summary

After the database schema modernization and service stabilization, the frontend listings ecosystem rendered **zero properties**, despite seeded data existing in the underlying PostgreSQL database. End-to-end investigations revealed a critical environment variable configuration mismatch in the Docker Compose setup and a database driver incompatibility in the search service. Both issues have been resolved, and the listings page is now fully functional across Grid, Map, and Detail views.

---

## 2. Root Cause Analysis

Two primary bugs blocked the search service from querying and serving properties:

### A. Environment Variable Mismatch (`DATABASE_URL` vs `DATABASE_SYNC_URL`)
- The `docker-compose.yml` configuration passed `DATABASE_SYNC_URL` to `search_service` and `geo_amenity_service`.
- However, the code in `search_service/database.py` queried `DATABASE_URL`.
- Because `DATABASE_URL` was not set in the container's environment, `database.py` fell back to loading `.env` which set `DATABASE_URL` to `localhost:5432` (host connection).
- Inside the Docker network, the database is hosted at hostname `postgres`, not `localhost`. This mismatch caused the search service to throw `500 Connection Refused` errors whenever the gateway attempted to query it.

### B. Driver Option Incompatibility (`currentSchema`)
- Similar to the earlier authentication service crash, the `DATABASE_URL` passed in `docker-compose.yml` included a schema query parameter (`?currentSchema=search`).
- The `psycopg2` driver used by SQLAlchemy in the search service threw a `ProgrammingError: invalid connection option "currentSchema"`, causing database connection pool initialization to fail.

---

## 3. Resolution Steps

### A. Environment Configuration Correction
In `docker-compose.yml`, the environment block for both `search_service` and `geo_amenity_service` was updated to explicitly pass the correct `DATABASE_URL` pointing to the `postgres` container.

```yaml
    environment:
      - DATABASE_URL=postgresql://postgres:rentora_secure_password@postgres:5432/rentora
```

### B. Query String Sanitization (Psycopg2)
In `search_service/database.py`, defensive URL parsing logic was added to strip out driver-incompatible query parameters (like `currentSchema`) before initializing the database engine:

```python
# Strip currentSchema from connection string (psycopg2 incompatibility)
if "?" in DATABASE_URL:
    base_part, query_part = DATABASE_URL.split("?", 1)
    params = [p for p in query_part.split("&") if not p.startswith("currentSchema=")]
    if params:
        DATABASE_URL = base_part + "?" + "&".join(params)
    else:
        DATABASE_URL = base_part
```

### C. Services Rebuild
The affected containers were rebuilt and restarted:
```bash
docker-compose up -d --build search_service geo_amenity_service
```

---

## 4. Verification Results

- **API Verification:** Hitting `POST /search/properties` through the gateway returns `200 OK` with a payload containing all **15 seeded properties**.
- **Cypress E2E Testing:** Executed `listings_verification.cy.ts` E2E tests, verifying that:
  - **Grid View** correctly renders property cards (e.g. *Luxury Sea-View Apartment in Bandra*, *Cozy 1BHK in Indiranagar*).
  - **Map View** successfully toggles and initializes Leaflet.
  - **Property Detail** page opens and renders the property information, city, state, and price.
  - **Result:** **3/3 Specs Passed** successfully.
