# Sprint 9: Walkthrough — i18n, Commute & Advanced Features

## What Was Built
- React-i18next internationalization with English and Hindi support
- Commute scoring display on property cards
- Featured properties carousel on listings page
- Advanced filtering with amenity chips and sort options

## Key Files
- `frontend/src/i18n/` — Translation configuration and locale files
- `frontend/src/components/Layout.tsx` — Language switcher added
- `frontend/src/pages/Listings.tsx` — Enhanced filters and sort
- `frontend/src/components/PropertyCard.tsx` — Commute badges

## i18n Implementation
- `useTranslation()` hook used across all pages
- Translations: `en.json`, `hi.json`
- Language switcher in navigation drawer
- All user-facing strings externalized

## Commute Scoring
- Time-based commute scores to offices, transit, schools
- Displayed as badges on property cards
- Color-coded: green (< 15 min), yellow (15-30), red (> 30)

## Advanced Features
- Featured carousel at top of listings page
- Amenity chip filter (WiFi, Parking, Gym, Pool, etc.)
- Sort by: Price (low/high), Newest, Relevance
