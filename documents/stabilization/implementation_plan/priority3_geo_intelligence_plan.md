# Implementation Plan: Priority 3 — Geo Intelligence & Spatial Platform Architecture

This plan documents the design and execution strategies to transform Rentora into an advanced, geo-intelligent proptech platform using MapLibre GL JS, PostGIS, Overpass API, OpenRouteService, and Redis GEO.

---

## 📋 Proposed Components & Objectives

### 1. Map Platform Migration (Leaflet to MapLibre GL JS)
- **MapLibre Integration**: Remove `leaflet`, `react-leaflet`, and `react-leaflet-cluster` completely from the frontend.
- **Vector Rendering**: Leverage `maplibre-gl` to render vector tiles natively, defaulting to light/dark themes (`streets-v2` / `darkmatter`) using MapTiler's vector styles.
- **Custom React Map Component**: Replace `frontend/src/components/MapView.tsx` and map views inside `frontend/src/pages/PropertyDetail.tsx` with high-performance, canvas-based MapLibre renders.
- **Backward-Compatible Cypress Selectors**: Preserve outer `div` wrappers with the class `.leaflet-container` to guarantee all existing Cypress integration tests pass without modifications.
- **Premium UX Enhancements**: Add dynamic animated transitions (`flyTo`), marker clustering, high-density point rendering, HTML hover preview cards, and mobile gestures.

### 2. PostGIS Spatial Engine
- **Spatial Columns & Indexes**: Extend `Property` and create new models (`metro_stations`, `hospitals`, `schools`, `office_hubs`, `locality_boundaries`) with geography `geom` point/polygon fields (SRID `4326`). Create `GIST` spatial indexes repo-wide.
- **Automatic Ingestion Pipelines**: Integrate automatic WKT conversions during property ingestion/updates to calculate `geom` values instantly using `ST_SetSRID(ST_MakePoint(lng, lat), 4326)`.
- **Query Replacement**: Replace all legacy math/haversine application code in `property_service/main.py` with index-accelerated PostGIS filters:
  - Proximity filter: `ST_DWithin`
  - Exact Proximity Sort: `ST_Distance`
  - Boundary filters: `ST_Contains` / `ST_Within`

### 3. Dedicated `geo_amenity_service` & Overpass Ingestion
- **New Microservice**: Build `geo_amenity_service` (FastAPI) as a standalone engine under schema `geo_amenity`.
- **Overpass API Integration**: Automate ingestion from OpenStreetMap via the Overpass API for amenities (schools, hospitals, transit stops, malls, grocery stores, cafes) in customized radii (500m, 1km, 2km, 5km).
- **Normalization Pipeline**: Parse and normalize category names, drop duplicates, and geo-deduplicate POIs.
- **Refresh Worker**: Introduce scheduled worker loops inside `geo_amenity_service` to refresh cached POIs periodically.

### 4. Commute & Routing Intelligence Engine
- **OpenRouteService Integration**: Query OpenRouteService (ORS) dynamically inside `geo_amenity_service` to calculate exact commute matrix elements (driving, walking, cycling) between properties and destination landmarks.
- **Commute Scoring**: Calculate exact commute duration/routes for "within 30 mins of tech park", "near metro", etc.
- **Commute Matrix Cache**: Cache routes and ETA estimations in Redis with custom TTL configurations.

### 5. Rentora Smart Locality Engine™
- **Weighted Connectivity Scores**: Create a locality analysis scoring system across various categories:
  - `metro_connectivity` (transit access)
  - `health_access` (hospital proximity)
  - `lifestyle_score` (nightlife, cafes)
  - `family_score` (green coverage, schools)
  - `commute_score` (average travel time)
- **Tenant Preference Configurations**: Allow customized weights by tenant profile (e.g. family priorities vs. nightlife/commute) and return ranked metrics dynamically.

### 6. Advanced Geo Search & viewports
- **Map Viewport Filter**: Expose viewport coordinate boundaries (bounding box `min_lat, min_lng, max_lat, max_lng`) inside spatial queries.
- **Custom Viewport Polygon Search**: Implement `ST_Contains` polygon drawing capability.
- **Autocomplete Indexing**: Provide rapid search autocomplete of localities, stations, and tech parks.

### 7. Geo Event & Redis Cache Optimization
- **RabbitMQ Integration**: Broadcast spatial update events: `property_geo_updated`, `locality_score_updated`, `amenity_cache_refreshed`.
- **Redis GEO Engine**: Leverage Redis `GEOADD` and `GEOSEARCH` to perform lightning-fast hot geo cache queries for amenities and commute matrices.

---

## 🛠️ Verification & Testing Plan
- **Mock Overpass/ORS**: Implement resilient local mock fallbacks if external API servers fail or are unconfigured.
- **PostGIS Health Probe**: Add a robust PostGIS/ORS connectivity health probe inside the Gateway diagnostics `/diagnostics` endpoint.
- **Automated Tests**: Confirm API and frontend models build perfectly. Verify all vector layouts render with zero visual artifacts.
