# Rentora — Enterprise Geospatial Rental & Commute Intelligence Platform

Rentora is a next-generation, high-performance geospatial rental platform built on a decentralized microservices architecture. It combines advanced PostGIS geospatial indexing, full-text search vector matching, real-time OpenStreetMap road-routing engines (OSRM), and modern responsive UI design. Rentora is designed to redefine how tenants discover properties and analyze their daily commutes, providing precise road-following travel durations and localized amenity mapping.

---

## 1. Project Overview

### Vision & Platform Strategy
Modern property portals often fall short by showing distances "as the crow flies," leading tenants to rent properties that seem nearby but require lengthy commutes due to geographical barriers, one-way streets, or traffic bottlenecks. 

Rentora solves this by integrating **Real Road Commute Intelligence** directly into the search and discovery phase. Our platform empowers users to evaluate properties based on actual walking, cycling, and driving routes using real road networks, paired with localized amenity density scoring.

```
+-----------------------------------------------------------------------------------+
|                                 TENANT WORKFLOW                                   |
|                                                                                   |
|  [Search / Filter] ---> [Grid & Map Views] ---> [Interactive Detail View]         |
|           |                     |                         |                       |
|           v                     v                         v                       |
|   Filter by Price,      Toggle listings on      Select nearby amenities           |
|   Locality, Type        MapLibre interactive    (Pharmacy, Bus Stop, etc.)        |
|                         canvas with markers     & view OSRM real-road routes      |
+-----------------------------------------------------------------------------------+
|                                 OWNER WORKFLOW                                    |
|                                                                                   |
|  [Property Registration] ---> [Media Upload] ---> [Contract Management]           |
|           |                         |                        |                    |
|           v                         v                        v                    |
|   Provide Title, Price,     Upload property images   Generate digital rental      |
|   Address, Geo Coords       to secure S3/local       agreements directly          |
|                             storage volumes          on the portal                |
+-----------------------------------------------------------------------------------+
```

### Core Platform Capabilities
- **Geospatial Property Search:** Real-time radius and bounding-box queries using PostGIS-indexed coordinates.
- **Microservices-driven Architecture:** Decoupled, independent services communicating securely through a unified API Gateway.
- **Smart Amenity Discovery:** Automatic mapping of surrounding POIs across 16 categories using live OpenStreetMap Overpass queries.
- **commute score Calculation:** A proprietary rating engine mapping real travel durations to a 1–10 quality scale.
- **Transactional Consistency:** Isolated Postgres schemas mapping to specific services, preventing cross-domain database coupling.

---

## 2. Features Section

### Tenant Features
*   **Dynamic Listings Grid:** Filter, sort, and browse properties with high-definition image galleries.
*   **Geospatial Map Search:** Interactive map canvas with property pins, cluster maps, and bounds-based reloading.
*   **Commute Navigation Panel:** Real road routing for Walking, Cycling, and Driving travel modes to any chosen amenity.
*   **Detailed Nearby Amenities:** List of surrounding points of interest categorized by proximity.
*   **Wishlist Support:** Save favorites to user profiles for subsequent review.

### Owner Features
*   **Listing Management:** Register, edit, and delete properties with specific coordinates and custom address details.
*   **Media Gallery Manager:** Upload and manage property images and videos with auto-generated thumbnails.
*   **Rental Agreement Generator:** Draft lease agreements on-demand using standardized legal templates and tenant details.
*   **Host Analytics Dashboard:** Track property views, lease history, and generated income.

### Admin Features
*   **Platform Health Dashboard:** Live monitoring of all 15+ microservices and backing databases.
*   **System-Wide Diagnostics:** Real-time logging, connection checking, and service uptime diagnostics via a centralized portal.
*   **User Role Auditing:** Manage system access roles (Admin, Tenant, Host) securely.

### Geo/Map Features
*   **OpenStreetMap Integration:** Fetch and parse nodes and ways directly from OSM via Overpass API.
*   **Road-Network Commute Router:** Integration with OpenRouteService (ORS) and OSRM for authentic routing shapes.
*   **High-FPS Marker Layer:** Native MapLibre vector layers for rendering high-density interactive pins without performance lag.
*   **Dynamic Viewport Filtering:** Auto-refresh listings in the sidebar as the user pans or zooms the map.

### Search Features
*   **Full-Text Search Indexing:** TSVector indexing for text matching on property titles, descriptions, and localities.
*   **Autocomplete Suggestions:** Prefix search for properties, localities, and landmarks.
*   **Multi-Attribute Filters:** Refine listings by pricing limits, room configurations, verification status, and commute distance.

### Authentication & Infrastructure Features
*   **JWT Security Handshake:** Access and refresh token cycle with secure backend signature validation.
*   **Docker Containerization:** Seamless multi-container setups supporting development, staging, and production environments.
*   **Resilient Fallbacks:** Fallback logic on API failure for offline development mode.

---

## 3. Complete Tech Stack

| Category | Technology | Purpose | Key Benefits |
| :--- | :--- | :--- | :--- |
| **Frontend** | React (v18) | Component-based User Interface | Declarative rendering, virtual DOM speed |
| | TypeScript | Static Typing & Code Safety | Eliminates runtime type errors, improves IDE autocomplete |
| | Vite | Frontend Build Tool | High-speed hot module replacement (HMR), optimized bundling |
| | MUI (Material-UI) | UI Component Library | Professional, responsive, customizable grid & input controls |
| | MapLibre GL | Vector Map Rendering | GPU-accelerated canvas mapping, smooth zoom & pan |
| **Backend** | FastAPI | High-performance Web APIs | Async/await syntax, built-in Swagger/OpenAPI docs, fast execution |
| | Python (v3.10) | Main Programming Language | Rich ecosystem, concise syntax |
| | SQLAlchemy | Object-Relational Mapper (ORM) | Database agnostic interface, secure parameterized queries |
| | Pydantic | Schema Data Validation | Strict data parsing, automated error responses |
| **Database** | PostgreSQL | Relational Database Engine | ACID compliance, enterprise robustness |
| | PostGIS | Geospatial Database Extension | Native spatial indexes (GIST), geometric shapes and calculations |
| | TSVector Index | Full-Text Search Engine | Rapid lexical index matching, ranking and stemming support |
| **DevOps** | Docker | Containerization Engine | Application isolation, repeatable developer environments |
| | Docker Compose | Service Orchestrator | Multi-container coordination, simplified service start sequences |
| | Nginx / FastAPI Gateway | Central API Proxy | Rate limiting, unified routing pathing, unified CORS controls |
| **Routing** | OSRM / ORS | Road-Routing Engine | Calculates real-road distance matrices and geometry tracks |
| | Overpass API | OpenStreetMap Data Fetcher | Searches and extracts real-world points of interest (POIs) |
| **Testing** | Cypress | End-to-End Testing | Visual browser automation testing |

---

## 4. System Architecture

Rentora is structured as a distributed microservice application. All service requests flow through a central Gateway, which acts as the system reverse-proxy, ensuring uniform CORS headers, correlation ID tagging, and IP-based rate limiting.

```
                                    +--------------------+
                                    |    React Client    |
                                    +---------+----------+
                                              |
                                              | HTTPS Requests
                                              v
                                    +--------------------+
                                    |    API Gateway     |
                                    |     (Port 8000)    |
                                    +----+--+---+---+----+
                                         |  |   |   |
         +-------------------------------+  |   |   +--------------------------------+
         |                                  |   |                                    |
         v                                  v   v                                    v
+------------------+    +----------------search_service-----+    +----------------geo_amenity_service+
|   auth_service   |    | - Search Indexing (Full-Text)    |    | - OSRM Router (walking/car/bike)  |
| - JWT issuance   |    | - Viewport Geospatial Queries    |    | - Overpass API POI Fetcher        |
| - Bcrypt hashing |    | - Syncs listings via Postgres    |    | - commute score Calculator        |
| (Port 8001)      |    | (Port 8015)                      |    | (Port 8014)                       |
+--------+---------+    +-------------------+---------------+    +-------------------+---------------+
         |                                  |                                        |
         |                                  |                                        |
         +-----------------------------+    |    +-----------------------------------+
                                       |    |    |
                                       v    v    v
                                  +--------------------+
                                  | PostgreSQL+PostGIS  |
                                  | - auth schema      |
                                  | - property schema  |
                                  | - search schema    |
                                  | - geo_amenity schema|
                                  +--------------------+
```

### Microservice Responsibilities
1.  **`gateway` (Port 8000):** Validates rate limits, appends correlation IDs for request tracing, and routes endpoints to the target microservice based on URL prefix pathing.
2.  **`auth_service` (Port 8001):** Manages user registrations, role definitions, and issues signed HS256 JWT tokens. Uses `bcrypt` with 12 rounds for password hashing.
3.  **`profile_service` (Port 8002):** Manages user profile details, favorites/wishlists, and tenant history records.
4.  **`property_service` (Port 8003):** The source-of-truth service for all listings. Manages registration, media uploads, and exposes `/location/pois` to fetch nearby landmarks.
5.  **`geo_amenity_service` (Port 8014):** The core geospatial intelligence unit. Integrates with OSRM and Overpass, computes commute scores, and exposes routing APIs.
6.  **`search_service` (Port 8015):** Exposes optimized read-only listing search APIs using PostgreSQL full-text search indexing and spatial index bounding envelopes.
7.  **`agreements_service` (Port 8008):** Manages digital rental contract lifecycle, rent terms, and contract generation.
8.  **`notification_service` (Port 8013):** Dispatches asynchronous alerts to users regarding agreement sign-offs and payments.

---

## 5. Architecture Diagrams

### Detailed End-to-End Request Flow
This diagram illustrates the path a client request takes when calculating a commute route to a nearby hospital:

```
[React App]                       [Gateway]                [geo_amenity]               [OSRM Demo]
    |                                 |                          |                          |
    |-- GET /geo/commute/route ------>|                          |                          |
    |   (lat, lng, mode)              |-- Forward Route Query -->|                          |
    |                                 |   (stripping /geo)       |-- Query Road Network --->|
    |                                 |                          |   (Bicycle/Foot/Car)     |
    |                                 |                          |                          |<-- Returns geometry --|
    |                                 |                          |-- Calculate travel time -|   & distance
    |                                 |                          |   using mode-speed multiplier
    |                                 |<-- Returns route JSON ---|                          |
    |<-- Returns HTTP 200 ------------|   (dist, duration, geom)
    |
```

### Search Index Synchronization
```
[User Registration/Update] ---> [property_service] 
                                       |
                                       | Writes properties table
                                       v
                                [Shared Database] 
                                       |
                                       | Database Triggers / Cron updates search.property_index
                                       v
                                [search_service] <--- Read-Only Search Requests <--- [Client App]
```

---

## 6. Database Design

Rentora utilizes a single PostgreSQL instance segmented into distinct schemas to maintain clean microservice separation while benefiting from ACID compliance.

```
                                  +-------------------------+
                                  |    PostgreSQL Instance  |
                                  +-------------------------+
                                               |
         +--------------------+----------------+--------------------+--------------------+
         |                    |                                     |                    |
         v                    v                                     v                    v
+------------------+ +------------------+                 +------------------+ +------------------+
|   auth schema    | | property schema  |                 |  search schema   | | geo_amenity sc.  |
| - users table    | | - properties     |                 | - property_index | | - amenity_points |
|                  | | - property_media |                 |                  | |                  |
+------------------+ +------------------+                 +------------------+ +------------------+
```

### Table Relationships and Definitions

#### `property.properties`
Exposes the main columns containing the master details of a registered home:
- `id` (INTEGER, Primary Key)
- `title` (VARCHAR)
- `description` (TEXT)
- `price` (NUMERIC)
- `address` (VARCHAR)
- `lat` (DOUBLE PRECISION)
- `lng` (DOUBLE PRECISION)
- `geom` (GEOMETRY Point, SRID 4326)
- `status` (VARCHAR, e.g. "available")

*Index Definition:*
```sql
CREATE INDEX idx_properties_geom ON property.properties USING GIST (geom);
```

#### `property.property_media`
Houses the image reference paths matching listings:
- `id` (INTEGER, Primary Key)
- `property_id` (INTEGER, Foreign Key -> `property.properties.id` ON DELETE CASCADE)
- `url` (VARCHAR)
- `is_featured` (BOOLEAN)

#### `search.property_index`
Highly optimized materialized table built for read-heavy search operations:
- `property_id` (INTEGER, Primary Key)
- `title` (VARCHAR)
- `price` (NUMERIC)
- `city` (VARCHAR)
- `geom` (GEOMETRY Point, SRID 4326)
- `search_vector` (TSVECTOR) — combining title, description, and city.

*Index Definitions:*
```sql
CREATE INDEX idx_property_index_geom ON search.property_index USING GIST (geom);
CREATE INDEX idx_property_index_search ON search.property_index USING GIN (search_vector);
```

---

## 7. Geosearch & Navigation Engine

### Amenity Discovery Logic (Overpass & Fallback)
When a property's coordinates are passed to `/property/location/pois`, the system calls `geo_amenity_service`'s `get_nearby_amenities`.
The engine maps OSM tag selectors to fetch nodes and ways inside a search envelope (default `3000m` radius):

```
       Radius (e.g. 3000m)
            _______
         .-'       '-.
       .'             '.
      /                 \
     |        (Property) | <--- Query Overpass API for:
     ;        [lat, lng] ;      - [amenity=school]
      \                 /       - [station=subway]
       '.             .'        - [shop=supermarket]
         '-._______.-'          - [amenity=pharmacy]
```

### Evolution of Real Road Routing
1.  **Phase 1 (Euclidean Baseline):** The initial implementation computed simple straight-line coordinates between the property and the amenity. This caused the route representation to overlap buildings and ignore rivers, bridges, or actual streets.
2.  **Phase 2 (OSRM Demo Integration):** We integrated the public OSRM engine (`router.project-osrm.org`) to fetch precise, road-matching coordinates.
3.  **Phase 3 (Speed & Mode Corrections):** OSRM raw duration metrics can skew towards driving profiles. We added mode-based travel speed calculations over the real road distance:
    -   **Walking:** 5 km/h (12.0 min/km)
    -   **Cycling:** 15 km/h (4.0 min/km)
    -   **Driving:** Taken directly from OSRM's real-time road conditions.

```
       STRAIGHT-LINE ROUTING                           REAL ROAD ROUTING (OSRM)
       
          Property [A]                                      Property [A]
               \                                                |____
                \  (Cuts through buildings)                      |   |___
                 \                                               |      |
                [B] Hospital                                    [B]-----* Hospital
```

---

## 8. Frontend Architecture

The Rentora frontend is a React application built with TypeScript and Vite. It utilizes Material-UI (MUI) for a high-quality styling theme, paired with MapLibre GL for dynamic canvas maps.

```
                                  +-------------------------+
                                  |       App Router        |
                                  |   (React Router Dom)    |
                                  +------------+------------+
                                               |
         +-------------------------------------+-------------------------------------+
         |                                                                           |
         v                                                                           v
+------------------+                                                        +------------------+
|   Listings Page  |                                                        |  Property Detail |
| - Listings Grid  |                                                        | - Map Canvas     |
| - Filter Panel   |                                                        | - Amenity Tabs   |
| - Map View       |                                                        | - Navigation Box |
+------------------+                                                        +------------------+
```

### Key UI Subsystems
*   **Map Marker Refinement:** The custom marker implementation dynamically scales pins using CSS transforms (`transform: scale(...)`) bound to the marker's inner element. This prevents marker displacement during map zooms and pans.
*   **Image Fallback Handling:** If external property images fail to load (e.g., dynamic Unsplash API limits), the `onError` handlers instantly swap the source to a styled local SVG fallback vector, maintaining UI consistency.
*   **Commute Time Component:** Refactored for robust display. Calculates travel estimates automatically from distance coordinates if direct backend time outputs encounter latency.

---

## 9. Backend Architecture

### FastAPI Microservice Design Pattern
Each microservice is designed using standard FastAPI practices, exposing separate routes, models, schemas, and database session lifecycles:

```
[Client Call] ---> [FastAPI Router] ---> [Route Handler] ---> [SQLAlchemy DB Session]
                          ^                     |
                          | (Pydantic Out)      v (Pydantic In)
                    [Pydantic Validation] <----+
```

-   **Asynchronous Database IO:** DB connection sessions are instantiated async on every request to avoid connection pooling issues.
-   **Docker Isolation:** Containers communicate over a virtualized Docker bridge network (`rentora_network`), keeping ports inaccessible externally except through port mappings on the host.

---

## 10. Authentication & Security

### Security Implementation Summary

```
[React Client]                      [Gateway]                    [auth_service]
      |                                 |                               |
      |-- POST /auth/login ------------>|-- Forward Login ------------->|
      |   (Username/Password)           |                               |-- Checks Bcrypt Hash
      |                                 |<-- Returns JWT token ---------|
      |<-- Stores token in LocalStorage-|
      |
      |-- GET /property/analytics ------>|
      |   (Authorization Bearer Header) |-- Validates HS256 JWT Signature
      |                                 |-- Extract User Roles (Admin/Host)
      |                                 |-- Forward request if verified
      |                                 |
```

*   **Secret Synchronicity:** All microservices use `"RENTORA_SUPER_SECRET_KEY"` paired with `"HS256"` encryption algorithm.
*   **Strict RBAC:** Endpoints like `/property/analytics/host` verify role arrays inside the JWT payload, returning `403 Forbidden` if unauthorized.

---

## 11. Installation Guide

### Prerequisites
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v20.10 or higher)
-   [Node.js](https://nodejs.org/) (v18 or higher)
-   [NPM](https://www.npmjs.com/) (v9 or higher)

### Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/rentora.git
cd rentora
```

#### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql://postgres:rentora_secure_password@postgres:5432/rentora
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
ENV=production
MAPTILER_KEY=VGr2EA4T8DcPNjZSXJos
JWT_SECRET=RENTORA_SUPER_SECRET_KEY
JWT_ALGORITHM=HS256
```

Create a `.env` file in the `frontend/` directory:
```env
VITE_API_URL=http://127.0.0.1:8000
VITE_MAPTILER_KEY=VGr2EA4T8DcPNjZSXJos
VITE_GOOGLE_MAPS_KEY=AIzaSyAD1FiET3WSUccLRpoKHeN3jDlyhFLeMkg
VITE_RAZORPAY_KEY_ID=rzp_test_MOCK_KEY
```

#### 3. Launch Services with Docker Compose
Start the Postgres, Redis, RabbitMQ, and all 8+ microservices:
```bash
docker-compose up -d --build
```

#### 4. Run Database Migrations & Data Seed
Run the master initialization script to prepare schemas, spatial tables, indexes, and insert dev mock records:
```bash
docker exec -it rentora_property_service python -m scripts.initialize_postgis
docker exec -it rentora_auth_service python -m scripts.seed_dev_data
```

#### 5. Start the Frontend Application
Navigate into the frontend directory, install dependency libraries, and run the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 12. Project Structure

```
rentora/
│
├── auth_service/               # Authentication & Authorization Microservice
│   ├── main.py                 # Service entry point & route registration
│   ├── database.py             # SQLAlchemy configuration
│   └── models.py               # Auth database models
│
├── geo_amenity_service/         # Geospatial & Navigation Intelligence Service
│   ├── main.py                 # Core routing, matrices & scores endpoints
│   ├── ors_client.py           # OSRM router integration
│   └── overpass_client.py      # OpenStreetMap Overpass client
│
├── property_service/           # Properties & Amenities Microservice
│   ├── main.py                 # Property listings and POI mapping APIs
│   ├── location/
│   │   ├── maptiler.py         # Autocomplete & local fallback data
│   │   └── provider.py         # Base provider class
│   └── schemas.py              # Pydantic validation schemas
│
├── search_service/             # High-speed search & autocomplete microservice
│
├── gateway/                    # API Gateway reverse proxy
│   └── main.py                 # Unified route proxying & rate-limiting middleware
│
├── frontend/                   # React Single-Page Application (SPA)
│   ├── src/
│   │   ├── api/                # API communication utility classes
│   │   ├── components/         # Reusable UI elements (Map views, Cards)
│   │   └── pages/              # Listing views, Dashboard, Detail pages
│   ├── cypress/                # Cypress End-to-End test suites
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml          # Docker Compose configuration file
└── README.md                   # Technical Documentation
```

---

## 13. API Documentation

### 1. Retrieve Nearby Points of Interest (POIs)
Returns a diverse list of nearby amenities within a specified radius.

*   **URL:** `/property/location/pois`
*   **Method:** `GET`
*   **Query Parameters:**
    -   `lat` (float, required): Latitude coordinate
    -   `lng` (float, required): Longitude coordinate
*   **Response Example (HTTP 200 OK):**
```json
{
  "pois": [
    {
      "name": "Women's Hospital",
      "lat": 19.0694023,
      "lng": 72.8306534,
      "category": "hospital",
      "distance": 891
    },
    {
      "name": "Wellness Forever",
      "lat": 19.0649138,
      "lng": 72.8298226,
      "category": "pharmacy",
      "distance": 910
    }
  ]
}
```

### 2. Calculate Commute Route
Calculates a road-following route between origin and destination coordinates.

*   **URL:** `/geo/commute/route`
*   **Method:** `GET`
*   **Query Parameters:**
    -   `origin_lat` (float, required)
    -   `origin_lng` (float, required)
    -   `dest_lat` (float, required)
    -   `dest_lng` (float, required)
    -   `mode` (string, required): `driving`, `walking`, `cycling`
*   **Response Example (HTTP 200 OK):**
```json
{
  "distance_km": 1.56,
  "duration_min": 2.7,
  "mode": "driving",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [72.822741, 19.068602],
      [72.822878, 19.068941],
      [72.830542, 19.069812]
    ]
  }
}
```

---

## 14. Testing & Validation

### Cypress E2E Visual Automation
To run automated end-to-end browser verification tests:
```bash
cd frontend
npx cypress run
```
Cypress validates grid view listing counts, map marker loads, and navigation interactions:

```
  Rentora Listings E2E Verification
    √ Verifies listings grid view rendering and data display (12.5s)
    √ Verifies toggle to map view and leaflet initialization (12.0s)
    √ Verifies navigation to property details page (16.3s)

  3 passing (42s)
```

---

## 15. Performance Optimization
-   **PostGIS spatial Indexing:** Uses `GIST` indexes on `geometry` columns to optimize distance and boundary searches.
-   **Materialized Search Views:** Consolidates data from properties, cities, and tags into a single read-optimized table.
-   **On-Demand Commute Calculations:** Avoids calculating routes for all nearby amenities during the initial page load. Instead, routes are calculated on-demand when a user clicks on an amenity.
-   **Redis Cache Layers:** Caches route geometry and travel duration queries for 24 hours.

---

## 16. Known Challenges & Fixes

### 1. Slow Route Pre-Computation
-   **Challenge:** The initial design pre-calculated commute routes for all POIs sequentially on listing detail page load, resulting in request timeouts (HTTP 504).
-   **Resolution:** Removed the route pre-calculation loop from `property_service`. The client now queries commute details dynamically only when a user selects a specific amenity marker or list item.

### 2. Map Marker Hover Displacement
-   **Challenge:** Hover animations on MapLibre markers caused them to displace or jitter.
-   **Resolution:** Restructured CSS selectors to scale the marker icon elements (`transform: scale(...)` on `firstElementChild`) rather than the absolute-positioned library wrapper div.

### 3. Blank Travel Time Displays
-   **Challenge:** Under certain latency conditions or OSRM request failures, the estimated time block showed blank values.
-   **Resolution:** Modified `formatCommuteTime` on the client side to parse multiple duration fields and automatically calculate a fallback duration using mode-specific speeds if duration is missing.

---

## 17. Future Roadmap
1.  **Direct Chat Services:** Web-socket based real-time messaging between hosts and prospective tenants.
2.  **In-App Payments:** Razorpay integration for security deposits and monthly rent payments.
3.  **Predictive Commute Models:** ML-based traffic predictions integrated into commute scores.

---

## 18. Contributing Guide

1.  **Coding Standards:** Follow PEP 8 for Python and ESLint guidelines for React/TypeScript code.
2.  **Commit Convention:** Use structured prefixes (e.g. `feat:`, `fix:`, `docs:`, `refactor:`).
3.  **PR Pipeline:** Ensure all Cypress tests pass before submitting a pull request.

---

## 19. License

This project is licensed under the MIT License:

```
MIT License

Copyright (c) 2026 Rentora Dev Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 20. Author / Credits
-   **Rentora Core Team:** Geospatial system architects and full-stack software engineers.
-   **Antigravity:** Codebase stabilization and UX refactoring agent.
-   **OSRM & OpenStreetMap Teams:** Backing routing and geographic data libraries.
