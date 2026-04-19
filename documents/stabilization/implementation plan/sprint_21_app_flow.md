# Implementation Plan - Sprint 21: Application Flow & Navigation

Restructure the application journey to prioritize security and role-specific utility.

## Key Changes
- **Auth Guard**: Introduced `ProtectedRoute` for mandatory JWT verification.
- **Role Routing**: Implemented automatic redirection to role-specific dashboards.
- **Unified UI**: Created `AppMenu` (Hamburger Drawer) for centralized feature access.
- **KYC Flow**: Enabled document upload and verification status tracking.
