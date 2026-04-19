# Implementation Plan - Sprint 21: Auth-First Flow & Role Dashboards

Restructure the application journey to prioritize security and role-specific utility.

## User Review Required

> [!IMPORTANT]
> I will be creating **three distinct dashboard components** to ensure that Tenants, Owners, and Admins have zero overlap in UI complexity and functionality.

## Proposed Changes

### 1. Frontend: Auth & Routing
#### [NEW] [ProtectedRoute.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/ProtectedRoute.tsx)
- Higher Order Component (HOC) to check `localStorage` for a valid token.
- Handles role-based access (e.g., preventing a tenant from accessing `/admin/dashboard`).

#### [MODIFY] [App.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/App.tsx)
- Set `/` to `LoginPage`.
- Wrap all sensitive routes (Dashboard, Profile, Listings) in `ProtectedRoute`.
- Add new role-specific routes: `/tenant/dashboard`, `/owner/dashboard`.

#### [MODIFY] [Login.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/Login.tsx)
- Update post-login navigation logic to redirect based on the `role` claim in the JWT.

### 2. Frontend: Unified Navigation
#### [NEW] [AppMenu.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/AppMenu.tsx)
- A unified Sidebar/Hamburger menu (using MUI Drawer).
- Items: Profile Edit, KYC, Digital Agreements, Notifications, Settings, and a dedicated **Logout** button.
- Role-aware logic: Hides/Shows items based on user role (e.g., "Add Property" for Owners only).

#### [MODIFY] [Layout.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/Layout.tsx)
- Integrate the new `AppMenu` and remove the legacy profile/logout trigger from the Avatar component.

### 3. Backend: Profile & KYC
#### [MODIFY] [profile_service/main.py](file:///d:/Python%20Projects/Rentaro/profile_service/main.py)
- Refine `PUT /` to ensure all fields from the frontend form are handled.
- Implement more robust error handling for document uploads.

---

## Verification Plan

### Automated Tests
- **Auth Guard Test**: Verify that navigating to `/owner/dashboard` while logged in as a `tenant` triggers a redirect to the home page or a 403.
- **Route Persistence**: Verify that clearing `localStorage` immediately redirects the user to `/login`.

### Manual Verification
1. **Entry Flow**: Open [http://localhost:5173/](http://localhost:5173/); confirm it shows the Login page.
2. **Dashboard Redirect**: Login as a `tenant`; confirm redirection to `/tenant/dashboard`.
3. **Menu Interaction**: Open the hamburger menu; confirm "Profile" navigates to the edit page without logging out. 
4. **KYC Submission**: Upload a mock ID and verify the `kyc_status` updates to `pending_review` in the Profile UI.
