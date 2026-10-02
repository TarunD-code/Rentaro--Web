# Sprint 3: Implementation Plan — Property Service & Listings

## Goal
Implement property management: CRUD operations, media upload with thumbnail generation, and browse listings page.

## Proposed Changes

### 1. Property Service (Port 8003)
- **Database**: `rentora_properties.db` (SQLite)
- **Models**:
  - `Property` — owner_id, title, description, address, property_type, price, amenities, is_featured, created_at
  - `PropertyMedia` — property_id, file_type, raw_url, thumb_url, mime_type, size
- **Endpoints**:
  - `POST /` — Create property (owner only)
  - `GET /` — List with filters (q, min/max_price, type, amenities, featured)
  - `GET /{id}` — Get property detail
  - `PUT /{id}` — Update property
  - `DELETE /{id}` — Delete property
  - `POST /{id}/media` — Upload media (images/videos)
- **Media Processing**: Thumbnail generation via mediaprocessor module

### 2. Frontend Pages
- CreateProperty page with multi-step form
- Listings page with filter sidebar and grid cards
- PropertyCard component with image carousel
- PropertyDetail page with full gallery

### 3. Gateway Update
- Add `PROPERTY_SERVICE_URL` and routing for `property/*`

## Verification
- Create property with images → See in listings → Filter/search → View detail
