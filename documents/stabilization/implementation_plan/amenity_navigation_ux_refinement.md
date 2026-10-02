# Implementation Plan: Amenity Navigation UX & Data Completeness Refinement

We will implement targeted refinement for the Property Detail and Nearby Amenities system to fix the blank estimated travel times, add the missing "Cycling" (Bike) commute mode, and ensure that all required amenity categories are correctly returned and rendered, even when fallback is active.

## Proposed Changes

### [Microservices]

#### [MODIFY] [main.py](file:///d:/Python%20Projects/Rentaro/property_service/main.py)
- Increase the HTTP timeout for calling the `geo_amenity_service` from `8.0` seconds to `25.0` seconds to prevent request timeouts during complex sequential queries.
- Remove the slow serial route pre-computation loop from the `/location/pois` endpoint, as routing calculations are now performed on-demand by the frontend when a user clicks on an amenity.
- Pass through the `distance` (meters) field to the frontend and limit the returned list to a maximum of 30 diverse POIs (up to 3 per category) for a clean UI presentation.

#### [MODIFY] [maptiler.py](file:///d:/Python%20Projects/Rentaro/property_service/location/maptiler.py)
- Enrich the `_mock_pois` fallback method to include all 16 required amenity categories (Pharmacy, Bus Stop, Bus Depot, Schools, Colleges, Playground/Parks, Offices/MNCs, Restaurants/Cafes, ATMs, Banks, etc.).
- Ensure that the local fallback database contains realistic distance values, so the app remains fully functional offline.

---

### [Frontend Components]

#### [MODIFY] [PropertyDetail.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/PropertyDetail.tsx)
- Add a new "Bike" travel mode button to the commute options using the `DirectionsBike` icon from MUI, enabling users to request cycling commute routing.
- Make the `formatCommuteTime` function extremely resilient by:
  - Checking multiple field name variations for duration (e.g. `duration_min`, `durationMin`, `duration_mins`, `duration`).
  - Automatically converting duration to minutes if it is returned in seconds (i.e. > 120 seconds).
  - Providing a fallback haversine-based calculation from `distance_km` if duration is missing or undefined (`walking` at 5 km/h, `cycling` at 15 km/h, `driving` at 35 km/h).
- Map all 16 categories correctly to their respective tab categories and MUI icons inside `getCategoryIcon` and `amenityCategories`.

---

## Verification Plan

### Automated Verification
- Query `/property/location/pois` with mock or active coordinates and verify that the response contains up to 30 diverse POIs covering the rich list of categories.
- Query `/geo/commute/route` for all three travel modes (`driving`, `walking`, `cycling`) and verify that they return a valid JSON object containing `distance_km` and `duration_min` fields.

### Manual Verification
- Launch the application, click on a property listing, and inspect the Nearby Amenities section.
- Select different categories and confirm that POIs are populated with their correct icons and distances.
- Click on individual amenities and toggle between Drive, Walk, and Bike travel modes.
- Verify that both the route polyline is drawn on the map and the Estimated Time / Distance boxes are filled with accurate, rounded time estimates (e.g. "8 mins", "14 mins", "3 mins").
