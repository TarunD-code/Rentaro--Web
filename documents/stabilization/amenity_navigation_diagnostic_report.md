# Diagnostic Report: Nearby Amenities Navigation Feature

**Path:** `documents/stabilization/amenity_navigation_diagnostic_report.md`  
**Date:** May 19, 2026  
**Status:** Investigation Complete

---

## 1. Executive Summary
The "Nearby Amenities Navigation" feature in Rentora is designed to allow users to click any nearby point of interest (POI) listed on the property details page and view a dynamic route/path from the property to that amenity. While POI markers are shown on the map and lists are populated, clicking them does not trigger routing.

This investigation identified three primary structural gaps across the frontend map presentation layer and the backend routing client that prevent this feature from functioning.

---

## 2. Layer-by-Layer Diagnostics & Root Causes

### A. Frontend Layer (`PropertyDetail.tsx` & `MapView.tsx`)
1. **Missing Click Handlers on POI Lists:**
   In [PropertyDetail.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/PropertyDetail.tsx#L482-L495), the nearby points of interest are mapped to static Grid boxes with no `onClick` listeners or selection states.
2. **Missing Click Handlers on Map Markers:**
   In [MapView.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/MapView.tsx#L249-L280), the POI markers are instantiated with only a hover-popup and have no click handler callback to select the POI.
3. **No Route Presentation Logic:**
   The inline `PropertyMap` component in `PropertyDetail.tsx` has no MapLibre layer or source of type `line` to display routing geometries, nor does it have any logic to bounds-fit the viewport to show both points.

### B. Backend Routing Client (`geo_amenity_service/ors_client.py`)
1. **Missing Geometry Payload in Response:**
   The `get_route` endpoint returns only `{ "distance_km": float, "duration_min": float, "mode": str }`. It completely omits the polyline coordinates or GeoJSON geometry returned by OpenRouteService (ORS).
2. **Euclidean Fallback Lack of Spatial Path:**
   When ORS API keys are not configured, the service falls back to `_estimate_route` which uses the Haversine formula but generates no coordinates list.

### C. Database & Infrastructure Status
- **PostGIS Geometries:** Verified that the `geom` columns on `property.properties` and `geo_amenity.amenity_points` exist and are indexed.
- **Microservice Routing:** Gateway proxies `/geo` requests to `geo_amenity_service` on port 8014 correctly, but the frontend currently makes no calls to this route endpoint.

---

## 3. Recommended Stabilization Actions
1. **Upgrade Backend Client:** Modify `ors_client.py` to query `/geojson` format directions to obtain route coordinates, and return standard GeoJSON LineString coordinates under a `geometry` field. Fall back to a straight line LineString for estimated routes.
2. **Implement Selection State:** Add `selectedPoi` and `commuteMode` state hook variables inside `PropertyDetail.tsx`.
3. **Build Route Renderer:** Update `PropertyMap` to add a MapLibre line layer using the GeoJSON path data and call `map.fitBounds()` when a route is loaded.
