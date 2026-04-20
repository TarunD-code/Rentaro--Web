# Implementation Plan: Sprint 21 Troubleshooting & Seeding

This plan addresses three critical areas: UI layering for map search, dependency resolution for the chat system, and unified development data seeding.

## User Review Required

> [!IMPORTANT]
> I will be creating a **Master Seed Script** (`scripts/seed_dev_all.py`) that populates multiple service databases (`rentora_auth.db`, `rentora_properties.db`, etc.). This assumes the user has the Python environment correctly configured to write to these SQLite files directly.

## Proposed Changes

### 1. Frontend: Map Layering & UI (Issue A)
#### [MODIFY] [SearchBar.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/SearchBar.tsx)
- Add `zIndex: 1100` to the suggestions `Paper`.
- Ensure `pointerEvents: 'auto'` is explicit on the portal children.
- Improve `onBlur` handling to prevent premature closing when clicking suggestions.

#### [MODIFY] [MapView.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/MapView.tsx)
- Add `zIndex: 0` to the `.map-container` via SX props to ensure it stays below overlays.

#### [MODIFY] [Layout.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/Layout.tsx)
- Add global CSS overrides for Leaflet containers if necessary to enforce z-index rules.

---

### 2. Frontend: Chat Stabilization (Issue B)
#### [MODIFY] [package.json](file:///d:/Python%20Projects/Rentaro/frontend/package.json)
- Add `socket.io-client` dependency.

#### [MODIFY] [ChatComponent.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/ChatComponent.tsx)
- Add defensive checks for `currentUser` props.
- Wrap socket initialization in a try/catch.
- Ensure the `SOCKET_URL` is configurable or has a robust fallback.

---

### 3. Backend: Master Dev Seed (Issue C)
#### [NEW] [seed_dev_all.py](file:///d:/Python%20Projects/Rentaro/scripts/seed_dev_all.py)
- A unified Python script that:
  - Seeds `auth_service` with Tenants, Owners, and Admins.
  - Seeds `property_service` with 50+ sample listings across key Bengaluru locations (Electronic City, BTM, etc.).
  - Seeds `notification_service` with unread messages.
  - Seeds `agreements_service` with sample drafts.
  - Uses existing logic from specialized seed scripts (`seed_payments.py`, etc.) where possible.

#### [NEW] [fixtures.json](file:///d:/Python%20Projects/Rentaro/scripts/fixtures.json)
- Data definitions for standard test identities and property templates.

## Verification Plan

### Automated Tests
- Run `node scripts/seed_dev_all.py` (or Python equivalent) and verify no integrity errors.
- Visual check on the Map page to ensure suggestions are selectable.

### Manual Verification
1. **Map Search**: Type "electronic" in search; confirm suggestions appear *over* the map and can be clicked.
2. **Messages**: Click "Messages" in the menu; confirm the chat interface loads without the "socket.io-client" module error.
3. **Data Check**: Log in as `admin@rentora.com` and confirm the Admin Dashboard shows non-zero metrics derived from the seed script.
