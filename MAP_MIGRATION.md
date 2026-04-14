# Map Migration Guide: MapTiler -> Google Maps

Rentora handles location services using an abstracted backend service layer (`property_service/location`) and generic Leaflet rendering modules to ensure seamless provider swapping during scaling.

Currently, **MapTiler** is serving Phase 1 map requests.

## How to execute Phase 2 Migration (Google Maps)

### Backend Update
1. **Implement `GoogleProvider`**: In `property_service/location/google.py`, replace the `NotImplementedError` stubs with actual Google Maps HTTP API calls:
   - `autocomplete()` -> Google Places Autocomplete API.
   - `geocode()` -> Google Geocoding API.
   - `fetch_pois()` -> Google Places API (Nearby Search).
   - `get_route()` -> Google Distance Matrix API.
2. **Environment Switch**: Update the environment variable on the server orchestrator:
   - Current: `MAP_PROVIDER=maptiler`
   - New: `MAP_PROVIDER=google`
3. Restart `property_service` via `uvicorn`. The `__init__.py` load balancer will automatically pick up `GoogleProvider`.

### Frontend Update
1. **Remove MapTiler Layer**: Inside `frontend/src/pages/Listings.tsx` and `frontend/src/pages/PropertyDetail.tsx`, change `<TileLayer url="...maptiler..."/>`.
2. **Install @react-google-maps/api**: If continuing with native Google Maps styling instead of Leaflet, install the React Google Maps wrapper.
3. Switch out generic leaflet `<MapContainer>` nodes for the Google `<GoogleMap>` rendering module.
4. Replace `.env` configurations:
   - Current: `VITE_MAPTILER_KEY=YOUR_MAPTILER_KEY`
   - New: `VITE_GOOGLE_MAPS_KEY=YOUR_GOOGLE_KEY`
