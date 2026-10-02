# PropertyCard Crash Fix & Defensive Normalization Report

This document reports the root cause, schema upgrades, frontend/backend changes, and validations performed during the Browse Listings Stabilization Sprint.

## 1. Root Cause Analysis
* **Symptom:** The Browse Listings page crashed on load with `TypeError: Cannot read properties of undefined (reading 'split')` at `PropertyCard.tsx:49`.
* **Investigation:** 
  1. The frontend listings page queries `POST /search/properties` which redirects requests to `search_service`.
  2. The database table `search.property_index` did not contain or return the `amenities`, `images`, `locality`, `bedrooms`, `bathrooms`, or `furnishing` columns.
  3. Consequently, the search service returned property dictionaries where these keys were completely undefined.
  4. In `PropertyCard.tsx`, the line `property.amenities.split(',')` executed on `undefined`, triggering a React component crash.

---

## 2. Infrastructure & Schema Changes

### 2.1 Database Column Upgrades
We modified `search.property_index` schema and the SQLAlchemy model `PropertyIndex` to include:
- `images` (TEXT): Comma-separated list of image URLs.
- `locality` (VARCHAR(256)): Extracted locality details.
- `bedrooms` (INTEGER): Bedroom counts.
- `bathrooms` (INTEGER): Bathroom counts.
- `furnishing` (VARCHAR(64)): Furnishing state.

### 2.2 Triggers and Stored Procedures
We registered triggers on `search.property_index` to automatically:
1. Standardize and generate the `geom` geometry point (for map view support) from `lat`/`lng` inputs.
2. Standardize and generate `search_vector` for full-text search indexing on `title`, `address`, `city`, and `amenities`.

---

## 3. Implemented Fixes

### 3.1 Backend Fixes (`search_service` & `scripts`)
* **[initialize_postgres.py](file:///d:/Python%20Projects/Rentaro/scripts/initialize_postgres.py) / [create_postgres_tables.py](file:///d:/Python%20Projects/Rentaro/scripts/create_postgres_tables.py)**: Added the `search` schema to the list of databases to initialize, ensuring the service works seamlessly out-of-the-box on new environment deployments.
* **[rebuild_search_index.py](file:///d:/Python%20Projects/Rentaro/scripts/rebuild_search_index.py)**: Applied structural migrations, mapped the triggers, and migrated images and metadata for all 15 seeded properties from `property.properties` to `search.property_index`.
* **[index_worker.py](file:///d:/Python%20Projects/Rentaro/search_service/index_worker.py)**: Upgraded RabbitMQ index worker queries to automatically map all new columns when real-time updates propagate.
* **[main.py](file:///d:/Python%20Projects/Rentaro/search_service/main.py)**: Upgraded SELECT fields and implemented robust parsing/safe default generation for all property response records.

### 3.2 Frontend Fixes (`frontend`)
* **[PropertyCard.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/PropertyCard.tsx)**:
  - Updated the `Property` interface definitions to support optional/fallback fields.
  - Implemented defensive parsing for amenities: `Array.isArray(property?.amenities) ? property.amenities : (property?.amenities || '').split(',')`.
  - Hardened image resolution logic to check the `images` array first, fallback to `thumbnail_url`, and then use a high-quality online property image placeholder if both are missing.
* **[Listings.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/Listings.tsx)**:
  - Hardened filtering logic: `(p?.title || '').toLowerCase().includes(...)` to handle null titles safely.
  - Standardized search pagination size requests to match backend Pydantic validation limits (`page_size: 50`).

---

## 4. End-to-End Validation
1. **API Check**:
   Hitted `/search/properties` directly. The endpoint successfully returned `200 OK` with 11 matching properties. The returned payloads properly mapped arrays of images, clean lists of amenities, and locality strings.
2. **Browser Validation**:
   - The listings page loaded perfectly on `http://localhost:5173/listings` with no console errors or React boundary crashes.
   - switching to Map View was successful, and search inputs instantly filtered listings (e.g. typing "Bandra" only displays the Bandra property card) without any errors.
