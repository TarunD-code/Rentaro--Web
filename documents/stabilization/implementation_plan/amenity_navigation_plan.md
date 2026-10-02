# Implementation Plan: Amenity Navigation Route Display

We will implement dynamic route drawing on the property detail map when a user clicks on an amenity. This requires updates to the backend route calculation service, the frontend page state, and the map rendering layer.

## Proposed Changes

### [Backend Services]

#### [MODIFY] [ors_client.py](file:///d:/Python%20Projects/Rentaro/geo_amenity_service/ors_client.py)
- Update `get_route` to query the ORS `/v2/directions/{profile}/geojson` endpoint to fetch the route coordinates as a GeoJSON LineString.
- Update `get_route` and `_estimate_route` to return a `"geometry"` field containing the GeoJSON LineString coordinates.

---

### [Frontend Components]

#### [MODIFY] [PropertyDetail.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/PropertyDetail.tsx)
- Define state for the selected amenity (`selectedPoi`) and the selected commute mode (`commuteMode`, defaulting to `'driving'`).
- Fetch route data dynamically from the `/geo/commute/route` endpoint when `selectedPoi` or `commuteMode` changes.
- Add UI controls (walking vs driving icons) and handle list item clicks so users can choose an amenity and travel mode.
- Render details of the active route (distance, duration) when a route is computed.
- Pass `selectedRoute` geometry data down to the `PropertyMap` sub-component.
- Modify the inline `PropertyMap` to:
  - Add/update a MapLibre GeoJSON LineString source and line layer when `selectedRoute` changes.
  - Dynamically fit the map's bounds using `map.fitBounds` so both the property and the amenity are visible.
  - Add click listeners to POI markers on the map to trigger amenity selection.

---

### [Diagnostic & Stabilization Documentation]

#### [NEW] [amenity_navigation_diagnostic_report.md](file:///d:/Python%20Projects/Rentaro/documents/stabilization/amenity_navigation_diagnostic_report.md)
- Create a complete end-to-end diagnostic report explaining the root causes (missing routing click handlers, lack of geometry coordinates in backend response, and missing MapLibre layers) and the stabilization steps.

## Verification Plan

### Automated Verification
- Verify that `geo_amenity_service` is running on port 8014.
- Query `/geo/commute/route` via Python to ensure the JSON response successfully includes the `"geometry"` field.

### Manual Verification
- Start all microservices and open the frontend app in the browser.
- Navigate to a property listing details page.
- Select/click different amenities in the list (e.g. Hospital, Metro Station) and toggle travel modes.
- Verify the map dynamically displays the route path and updates distance/duration info.
