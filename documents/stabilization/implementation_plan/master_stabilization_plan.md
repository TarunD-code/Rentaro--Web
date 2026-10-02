# Master Implementation Plan: App Startup & Manual Testing Stability

This plan addresses a series of critical runtime and infrastructure failures that prevent reliable manual testing of the Rentaro platform. It follows the comprehensive stabilization steps provided by the user.

## User Review Required

> [!IMPORTANT]
> This plan involves modifying the entry points of **multiple microservices** to add health checks and CORS middleware. This is necessary to resolve consistent 502/503/CORS errors seen during frontend-backend interaction.

## Proposed Changes

### 1. Frontend: Runtime Error Resolution
- **[MODIFY] [Layout.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/Layout.tsx)**: Add missing MUI imports (`Paper`, `BottomNavigation`, `BottomNavigationAction`) to fix the `ReferenceError`.
- **[MODIFY] [main.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/main.tsx)**: Wrap the `<App />` component in the `ErrorBoundary` to provide a resilient UI fallback.
- **[MODIFY] [App.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/App.tsx)**: Audit lazy loading paths for `ChatPage` and ensures routes align with the expected dashboard paths.

### 2. Backend: Infrastructure Guarding
- **[STABILIZE] Microservices**: Add a standardized `/health` endpoint and `CORSMiddleware` to the following services to ensure the API Gateway and Frontend can reliably interact with them:
    - [profile_service/main.py](file:///d:/Python%20Projects/Rentaro/profile_service/main.py)
    - [property_service/main.py](file:///d:/Python%20Projects/Rentaro/property_service/main.py)
    - [agreements_service/main.py](file:///d:/Python%20Projects/Rentaro/agreements_service/main.py)
    - [billing_service/main.py](file:///d:/Python%20Projects/Rentaro/billing_service/main.py)
- **[MODIFY] [gateway/main.py](file:///d:/Python%20Projects/Rentaro/gateway/main.py)**: Optimize `httpx` timeouts (to 60s) to prevent premature 502/503 errors during first-load cold starts.

### 3. Verification & Seeding
- **[EXECUTE]** `python scripts/seed_dev_all.py` to ensure fresh, valid `bcrypt` data exists for all roles (Admin, Owner, Tenant).
- **[BROWSER]** Perform a full smoke test:
    1.  Login as `admin@rentora.com`
    2.  Verify Dashboard metrics render (fixing MUI `Grid` size issues if any).
    3.  Verify Sidebar navigation and Messages flow.

## Open Questions

- **MUI Version**: `package.json` suggests @mui/material ^7.3.9, which is likely a typo for v6. Should I standardize the code to MUI v6 patterns (e.g., `<Grid size={...} />`)?

## Verification Plan

### Automated
- `curl -f http://localhost:8000/auth/health`
- `curl -f http://localhost:8000/profile/health` (after fix)

### Manual
1. Clear browser `localStorage` and `cookies`.
2. Access `http://localhost:5173/login`.
3. Submit `admin@rentora.com` / `password123`.
4. Confirm entry into Dashboard with visible charts/metrics.
