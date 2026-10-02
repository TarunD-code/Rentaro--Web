# Sprint 5: Implementation Plan — Google Maps Integration

## Goal
Integrate Google Maps into the Listings page with property markers, location autocomplete, and map/grid view toggle.

## Proposed Changes

### 1. Map Integration
- Google Maps JavaScript API with `@react-google-maps/api`
- Property markers with customized pins on map view
- Map/grid view toggle on Listings page
- MapPopupCard component showing property preview on marker click

### 2. Location Autocomplete
- Google Places Autocomplete for search input
- Location-based property filtering
- Geocoding for property coordinates

### 3. Listings Page Update
- Split view: grid view (default) + map view toggle
- Map view with clustered markers
- Click marker → popup card with property summary

## Verification
- Search location → Map centers to area → Markers show properties → Click marker shows popup
