# Sprint 3: Walkthrough — Property Service & Listings

## What Was Built
- Created `property_service` microservice on port 8003
- Full property CRUD with media upload and thumbnail generation
- Listings page with filters (price, type, amenities, search)
- PropertyCard and PropertyDetail components

## Key Files
- `property_service/main.py`, `models.py`, `schemas.py`, `database.py`, `media_processor.py`
- `frontend/src/pages/CreateProperty.tsx`, `Listings.tsx`, `PropertyDetail.tsx`
- `frontend/src/components/PropertyCard.tsx`

## Property Service Details
- **Property Model**: owner_id, title, description, address, property_type (apartment/house/villa/pg), price, amenities (comma-separated), is_featured
- **PropertyMedia Model**: property_id, file_type (image/video), raw_url, thumb_url, mime_type, size
- **Media Processing**: Auto-generates thumbnails on upload using PIL/Pillow
- **Filters**: Full-text search on title/address, price range, type, amenities

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create property (owner) |
| GET | `/` | List with filters |
| GET | `/{id}` | Property detail |
| PUT | `/{id}` | Update property |
| DELETE | `/{id}` | Delete property |
| POST | `/{id}/media` | Upload media |

## Frontend
- **CreateProperty**: Multi-step form with property details, amenities, photo upload
- **Listings**: Grid view with sidebar filters, responsive cards
- **PropertyDetail**: Full gallery, amenities list, owner info, contact button

## Database
- `rentora_properties.db` — Property + PropertyMedia tables
