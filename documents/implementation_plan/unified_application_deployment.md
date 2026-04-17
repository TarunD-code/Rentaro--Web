# Unified Application Deployment (Single URL)

The goal is to consolidate all Rentora services and the frontend under a single entry point (the Gateway) so the entire platform can be accessed via `http://127.0.0.1:8000`.

## User Review Required

> [!IMPORTANT]
> **Unified Access**: The Gateway will now serve the frontend production build directly. You will no longer need to run `npm run dev` or access port 5173 once this is deployed.

---

## Proposed Changes

### [Component] Gateway Integration

#### [MODIFY] [main.py](file:///d:/Python%20Projects/Rentaro/gateway/main.py)
*   **Static Mounting**: Add `app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")` at the end of the route definitions.
*   **SPA Catch-all**: Add a low-priority route to serve `frontend/dist/index.html` for all browser-handled paths (e.g., `/chat`, `/listings`) to ensure page refreshes work correctly.
*   **Service URLs**: Verify all upstream microservice URLs are correct for local background execution.

---

### [Component] Application Startup

#### [ACTION] Background Service Execution
*   Initialize and start the following services in the background using Antigravity's terminal:
    1.  Gateway (Port 8000)
    2.  Auth (Port 8001)
    3.  Profile (Port 8002)
    4.  Property (Port 8003)
    5.  Payment (Port 8004)
    6.  Maintenance (Port 8005)
    7.  Onboarding (Port 8006)
    8.  Communication (Port 8007)

---

## Open Questions

- None at this stage.

## Verification Plan

### Manual Verification
1.  Access `http://127.0.0.1:8000` in a browser.
2.  Verify the frontend loads correctly.
3.  Navigate to `/chat` or `/listings` and refresh the page to confirm SPA catch-all routing works.
4.  Perform a test login to confirm the single-URL Gateway properly routes traffic between frontend and backend services.
