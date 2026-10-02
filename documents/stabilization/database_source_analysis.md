# Database Source Analysis Report

**Date:** 2026-05-23  
**Status:** ✅ COMPLETED  

---

## 1. Active PostgreSQL Instance Details

The following table summarizes the parameters of the active database instance that the Rentora application is currently connected to:

| Parameter | Value | Details |
| :--- | :--- | :--- |
| **Hostname** | `postgres` | Resolved within the internal Docker bridge network |
| **Port** | `5432` | Exposed on the host machine as `127.0.0.1:5432` |
| **Database Name** | `rentora` | Centralized database for all schemas |
| **Container Name** | `rentora_postgres` | Docker container managing the PostgreSQL lifecycle |
| **Active Schemas** | `auth`, `profile`, `property`, `payment`, `maintenance`, `onboarding`, `communication`, `agreements`, `billing`, `owner_dashboard`, `subscription`, `support`, `notifications`, `search` | Multi-tenant schema design separation |

---

## 2. Docker vs. Local Database Divergence Investigation

### A. Port Conflict and Host Service Verification
- A verification check was executed on the host machine to check for a native PostgreSQL service running on port `5432`.
- `Get-NetTCPConnection` confirmed that port `5432` is bound to the process `com.docker.backend` (PID 24400), which represents the Docker host bridge.
- No local, host-based PostgreSQL daemon is running or conflicts with the container port.

### B. DATABASE_URL Resolution
- **Host resolution:** Hitting `localhost:5432` redirects traffic via WSL2 network relays straight into the `rentora_postgres` container.
- **Docker Compose resolution:** All microservices run inside the Docker network where the database container is addressable under host `postgres`. 
- **Active target database:** The application is connected to the database in the `rentora_postgres` container. There is no other divergent local DB in play.

---

## 3. Database Seed State Validation
- Running queries on the `rentora_postgres` database confirms the existence of the expected seeded rows.
- The `property.properties` table holds exactly **15 property records** (listed below), including:
  - *Luxury Sea-View Apartment in Bandra* (price 150,000)
  - *Cozy 1BHK in Indiranagar* (price 35,000)
  - *Premium Independent Villa* (price 250,000)
  - ... and 12 other properties spanning apartments, villas, studios, PGs, and commercial spaces.
- This confirms that the active database is the correct, fully-seeded database containing the test data.
