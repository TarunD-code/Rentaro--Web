# Issue 1 RCA & Implementation — Auth Guard & Landing Page Redirect

The application currently allows unauthenticated access to the dashboard and landing pages, bypassing the login flow. This plan implements a robust `ProtectedRoute` component and enforces a "Login First" landing page strategy.

## User Review Required

> [!IMPORTANT]
> **Landing Page Experience**: Accessing the root path `/` will now automatically redirect to `/login` if no valid token is found. If authenticated, the user is redirected directly to the `/dashboard`.

> [!NOTE]
> **Role-Based Redirects**: While `Dashboard.tsx` already handles role-specific views, we will ensure that the initial login redirect and the guard logic are fully role-aware.

---

## Proposed Changes

### [Component] Frontend Security

#### [NEW] [ProtectedRoute.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/ProtectedRoute.tsx)
*   Create a reusable component that verifies the presence of a JWT `token` and `role` in `localStorage`.
*   Redirect to `/login` if authentication is missing or expired.
*   Allow child routes to render only if authenticated.

#### [MODIFY] [App.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/App.tsx)
*   Wrap `/dashboard`, `/profile`, `/create`, `/payments`, `/maintenance`, `/onboarding`, `/payouts`, `/statements`, `/reconciliation`, and `/chat` within the `ProtectedRoute`.
*   Update the root route `/` to perform an logic-based redirect:
    *   `if (!authenticated) -> /login`
    *   `if (authenticated) -> /dashboard`

#### [MODIFY] [Login.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/Login.tsx)
*   Ensure that successful login stores the `token` and `role` before navigating to the dashboard.

---

### [Component] Backend Enforcement

#### [MODIFY] [profile_service/main.py](file:///d:/Python%20Projects/Rentaro/profile_service/main.py)
*   Ensure critical endpoints like `GET /profile/` and `GET /profile/notifications` strictly return `401 Unauthorized` if the `Authorization` header is invalid (verified).

#### [MODIFY] [property_service/main.py](file:///d:/Python%20Projects/Rentaro/property_service/main.py)
*   Ensure `GET /metrics` and `GET /agreements/user/list` are protected by the `get_current_user_info` dependency.

---

### [Component] CI/CD Pipeline

#### [MODIFY] [ci.yml](file:///d:/Python%20Projects/Rentaro/.github/workflows/ci.yml)
*   Update Node.js setup to version 24.
*   Add `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"`.
*   Add a test step: `npm run test:auth` (note: we may need to add this script to `package.json` if it doesn't exist).

---

## Open Questions

1. **Test Script**: Does the `test:auth` script already exist in `frontend/package.json`? If not, I will add a basic smoke test for the Auth Guard.

---

## Verification Plan

### Manual Verification
1.  **Sanity Check**: Open `http://127.0.0.1:8000/` in an Incognito window -> Expect redirect to `/login`.
2.  **Deep Link Guard**: Try accessing `http://127.0.0.1:8000/dashboard` directly -> Expect redirect to `/login`.
3.  **Authenticated Flow**: Login with `test@rentora.com` -> Expect redirect to `/dashboard`.
4.  **Role Verification**: Login as an 'owner' and verify the `OwnerDashboard` component is rendered properly.

### Automated Tests
*   `npm run build` (Verify Node 24 compatibility).
*   Run the new `npm run test:auth` if applicable.
