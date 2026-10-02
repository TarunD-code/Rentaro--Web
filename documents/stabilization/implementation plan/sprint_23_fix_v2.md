# Implementation Plan - Advanced Stabilization and Seed Engine (Archived)

This plan addresses the persistent "Access/Contract" issues identified in recent diagnostics, including 401/403/422/503 errors and runtime component crashes.

## User Review Required

> [!IMPORTANT]
> I will be creating a fresh database seeding script `scripts/seed_dev_data.py` which will replace existing data to ensure consistency across all services.
> I will also be consolidating the Notification routes to the standalone service on port 8013 to resolve the 503 errors.

## Proposed Changes

### [Component] Authentication & Security
- **Auth Service / All Services**: Ensure `SECRET_KEY` is synchronized to `"RENTORA_SUPER_SECRET_KEY"` and `ALGORITHM` is `"HS256"`.
- **Bcrypt Consolidation**: Standardize on 12 rounds for password hashing in both the seed script and the login handler.
- **Tenant Fix**: Explicitly test and verify the tenant login flow with hashed credentials.

### [Component] Property Service API
- **Metrics Schema**: Update `/metrics` to accept optional query parameters `owner_id` and `date_range` to support admin-level filtering.
- **RBAC Hardening**: Ensure `/analytics/host` returns `403 Forbidden` for users without the `admin` or `owner` role.

### [Component] Notification & Routing
- **Gateway Fix**: Re-route `/profile/notifications` to the dedicated `notification_service` on port 8013 if the internal Profile Service endpoint is deprecated or failing (503).
- **CORS Support**: Add explicitly allowed origins to the Notification Service if still seeing blocked requests.

### [Component] Frontend UI
- **ReferenceErrors**: Add missing `CircularProgress` and `Paper` imports to `HostAnalytics.tsx`, `AdminDashboard.tsx`, and `NotificationMenu.tsx`.
- **Fault Tolerance**: Wrap dashboard components in `ErrorBoundary` to prevent full-page crashes.
- **Protected Routes**: Verify that `ProtectedRoute.tsx` correctly handles role-based redirection.

### [Component] Data Seeding Engine
- **[NEW] [seed_dev_data.py](file:///d:/Python%20Projects/Rentaro/scripts/seed_dev_data.py)**:
    - 10 Tenant users (hashed passwords).
    - 10 Owner users (hashed passwords).
    - 10 Properties with realistic location and price data.
    - 10 Rental Agreements (varying statuses).
    - 10 Payment records (Rent & Deposits).
    - 10 Notifications per user.

## Verification Plan

### Automated Tests
- Run `scripts/verify_sprint23_fixes.py` (Extended to check new params).
- Verify database counts (Expect 10+ records per table).

### Manual Verification
- Perform Tenant Login via Browser.
- Verify Admin Dashboard renders without "Failed to fetch" (requires Gateway 8000 fix).
- Check Notification icon for count/list (Status 200).
