# Epic 3 — Landing Experience & Property Detail Engine

## Overview
This epic delivers two major user-facing features:
1. **Landing Page** (`/`) — High-conversion entry point with hero search and featured carousel
2. **Property Detail** (`/listings/:id`) — Rich property view with gallery, host card, and inquiry CTA

## Components Added

### Landing Page (`Home.tsx`)
- `HeroSearch` — Real-time autocomplete with debounced API calls to `GET /search/suggestions`
- `FeaturedCarousel` — Horizontal scroll of featured properties from `GET /properties?featured=true&limit=6`
- JSON-LD structured data for SEO
- Analytics event hooks for hero searches and CTA clicks

### Property Detail (`PropertyDetail.tsx`)
- Lazy-loaded image gallery with WebP support
- Host profile card with trust badge
- Amenities grid with iconography
- Sticky inquiry sidebar with CTA
- Related listings section
- Full SEO meta via `react-helmet-async`

### Media Pipeline (`media_processor.py`)
- Automatic WebP conversion on upload
- Server-side resizing to 1200×800
- Presigned URL generation for CDN delivery

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/properties?featured=true&limit=6` | Featured listings for carousel |
| GET | `/properties/{id}` | Full property detail with media[] |
| GET | `/search/suggestions?q=` | Autocomplete for hero search |

## Feature Flags
- `landing_v1` — Gates the new landing page
- `property_detail_v1` — Gates the property detail view
