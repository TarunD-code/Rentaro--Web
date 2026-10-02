# Implementation Plan — Navigation ETA & Amenity Enhancement

Refine the Property Detail and Nearby Amenities system to fix the blank estimated travel times, display all 8+ amenity categories, show a professional detail page header, and improve amenity naming realism.

## User Review Required
> [!IMPORTANT]
> - **Commute ETA Format:** Implements a helper function `formatCommuteTime` on the frontend that converts duration values (supporting both backend `duration_min` and provider `duration`) to human-readable strings (e.g., "5 mins" or "1 hr 10 mins").
> - **Amenity Categories Grouping & Filtering:** Adds category tabs/chips to the UI allowing the user to filter nearby amenities on both the list and the MapLibre map by Healthcare, Education, Transport, Food, Offices, Recreation, and Banking.
> - **Property Detail Header:** Adds a prominent Airbnb-style hero header section at the top of the detail page (above the gallery) showing the Title, Full Address/Location, Price, and Property Type.
> - **OSM Service Integration:** Cleans up `property_service` POI retrieval by forwarding requests directly to `geo_amenity_service`, which returns realistic city-contextualized names (Mumbai/Bengaluru) when OSM/Overpass is offline.

---

## Proposed Changes

### Backend Components

#### [MODIFY] [overpass_client.py](file:///d:/Python%20Projects/Rentaro/geo_amenity_service/overpass_client.py)
- Expand `CATEGORY_TAGS` to include `bus_stop`, `bus_station`, `bus_depot`, `cafe`, `bank`, `atm`, `playground`, `university`, `company`, and `tech_park`.
- Update `mock_amenities` to detect city coordinate bounds (Mumbai vs Bengaluru) and return realistic local establishment names (e.g. "Apollo Pharmacy", "Lilavati Hospital", "Nexus Mall Koramangala", "WeWork BKC") instead of generic numeric names.

#### [MODIFY] [schemas.py](file:///d:/Python%20Projects/Rentaro/property_service/schemas.py)
- Add `full_address: Optional[str] = None` to the `AddressDetail` serialization schema.

#### [MODIFY] [main.py](file:///d:/Python%20Projects/Rentaro/property_service/main.py)
- Include `full_address` in the `get_property_detail` address formatting block.
- Update `/location/pois` endpoint to fetch rich POIs from `geo_amenity_service`'s `/amenities/nearby` API, falling back to local providers if the service is down.

---

### Frontend Components

#### [MODIFY] [PropertyDetail.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/PropertyDetail.tsx)
- Import additional Material UI icons: `LocalHospital`, `School`, `ShoppingBag`, `Work`, `Park as ParkIcon`, `LocalPharmacy`, `Restaurant`, `LocalAtm`, `FitnessCenter`, and `Chip`.
- Implement `formatCommuteTime` helper function to handle duration and duration_min formatting (e.g., "12 mins", "1 hr 5 mins").
- Implement `getCategoryIcon` helper function to return appropriate MUI icons for different POI categories.
- Introduce `activeCategoryTab` state to group and filter POIs by Healthcare, Education, Transport, Food, Offices, Recreation, and Banking.
- Add scrollable Chips to allow users to filter POIs list and map markers.
- Add an Airbnb-style hero header above the Gallery rendering title, full address, property type chip, and formatted monthly price.

---

## Verification Plan

### Automated / API Verification
- Query `GET http://localhost:8000/property/location/pois?lat=19.0688&lng=72.8222` to verify that 8+ categories are returned with realistic Mumbai-specific names.
- Query `/geo/commute/route` to ensure driving, cycling, and walking response payload contains correct distance and duration.
- Re-run Cypress regression specs.

### Manual Verification
- Open property detail page (e.g., `/listings/1`) and confirm the hero header displays the title, full address (e.g. "Carter Road, Bandra West"), price, and property type.
- Click on an amenity tab (e.g., Transport) and verify the list and map filter to show only transport POIs.
- Click on a POI and verify the estimated commute duration displays correctly for driving and walking modes (e.g., "8 mins", "23 mins").
