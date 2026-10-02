# Implementation Plan — Platform Fixes & Rentora Upgrades

This plan details the technical solution for the four platform fixes across the Rentora workspace:
1. **KYC UI Refinement & Media Capture Pipeline**: Dynamic button states, webcam capture via getUserMedia, drag-and-drop zones, and signature drawing pad.
2. **Admin Authentication Routing & Report Scheduling**: Admin routing checks, admin-exclusive KYC metrics audit component, and FastAPI backend routes for records fetch and background report generation/SMTP delivery.
3. **Map View Polyline Route Rendering**: Drawing navigation routes between the property and clicked amenities using MapLibre GL.
4. **Complete Rental Agreement Wizard**: Implementing the 5-step industry-standard rental agreement builder in React TypeScript.

---

## Task 1: KYC Component UI Refinement & Media Capture Pipeline

### Frontend Changes
We will update [KYCVerificationFlow.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/KYCVerificationFlow.tsx):
- **Dynamic Button States**:
  - Implement a helper `isVerificationInfoValid` checking the length of Aadhaar (12 digits) and validity of PAN (10-char alphanumeric).
  - Toggles between `variant="outlined"` (cancel-like appearance: transparent background, neutral border, text color) and `variant="contained"` (primary brand blue, white text) for Consent step (based on `consentChecked`) and Verification Info step (based on validity).
- **Webcam Section**:
  - Add native browser stream using `navigator.mediaDevices.getUserMedia`.
  - Display video stream inside a styled box, allowing users to "Capture Photo" (takes canvas snapshot, saves as base64 data URL) and "Retake".
- **Drag and Drop Files**:
  - Add file upload zones for Aadhaar card, PAN card, and signature upload.
  - Display status indicators showing file name, size, or green checkmark once uploaded.
- **Signature Canvas Sketchpad**:
  - Integrate an HTML5 `<canvas>` sketchpad with mouse/touch listeners allowing users to sign directly.
  - Add a "Clear Signature" button.

---

## Task 2: Admin Authentication Routing & Report Scheduling Engine

### Role-Based Routing Isolation
We will update:
- [KYCVerificationFlow.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/KYCVerificationFlow.tsx)
- [OnboardingForm.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/OnboardingForm.tsx)
- [AgreementPage.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/AgreementPage.tsx)
- Add a `useEffect` on each to inspect the stored role in localStorage:
  ```typescript
  useEffect(() => {
    const role = localStorage.getItem('role');
    if (role === 'admin' || role === 'ADMIN') {
      navigate('/admin/dashboard');
    }
  }, [navigate]);
  ```

### Backend Report Engine (FastAPI)
We will update `kyc_service` files:
1. **[schemas.py](file:///d:/Python%20Projects/Rentaro/kyc_service/schemas.py)**:
   - Add `AdminKYCRecord` Pydantic model for record serialization.
   - Add `ReportScheduleRequest` and `ReportScheduleResponse` models.
2. **[main.py](file:///d:/Python%20Projects/Rentaro/kyc_service/main.py)**:
   - Add JWT-verifying role dependency `get_current_admin` that checks if the JWT claim `role` matches `"admin"` or `"ADMIN"`.
   - Add `GET /api/v1/admin/kyc/records` returning all records for auditing.
   - Add `POST /api/v1/admin/reports/schedule` using `BackgroundTasks` to fetch user metadata, generate CSV/PDF validation summary, and trigger SMTP mail agent delivery (with a resilient fallback to printing/logging/saving to a local file if SMTP parameters are missing).

### Admin Management Portal Component
We will update [AdminDashboard.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/dashboards/AdminDashboard.tsx):
- Add a dedicated styled KYC Auditing panel.
- Implement an API call to load user KYC records (`/kyc/api/v1/admin/kyc/records`).
- Display detailed tables with user email, masked Aadhaar/PAN, status, facial score, timestamps.
- Add an action button to "Schedule/Email Audit Report" invoking the backend `POST /api/v1/admin/reports/schedule` endpoint.

---

## Task 3: Map View Polyline Route Rendering

We will fix [PropertyDetail.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/PropertyDetail.tsx):
- **Map Effect Hook**:
  - The map implementation inside `PropertyDetail.tsx` (the `PropertyMap` component or equivalent) needs to listen to `selectedRoute` or the click on an amenity card.
  - When coordinates from the OSRM road route payload response are available, we will programmatically check if the MapLibre instance has a layer/source for the route.
  - If a route already exists, we will clear it (remove layer and source) or update it using `.setData()`.
  - Draw a sharp path line from the source property coordinates to the clicked destination amenity using a `line` layer with specific colors and thicknesses.

---

## Task 4: Complete Rental Agreement Wizard

We will implement the complete agreement builder wizard:
- Update [AgreementBuilder.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/Agreement/AgreementBuilder.tsx) to provide a 5-step wizard with shared React state object `agreementData`:
  1. **Contract Details**: property location,refundable security deposit, agreement timeframe (6 vs 11 months), maintenance exclusions.
  2. **Property Details**: independent house, apartment, commercial shop, floor indexing, building tags, structural details.
  3. **Landlord Details**: legal name, age, gender, contact number, permanent address, masked tax id.
  4. **Tenant Details**: tenant identifiers, contact, validation state.
  5. **Summary & Selection Panel**: legal drafting expenses estimate, clause picker for popular pre-baked terms (Painting charges, Water & Electricity, Pet policies), and a signature panel.

---

## Verification Plan

### Automated Tests
- Run backend unit tests inside `kyc_service` using `pytest`.
- Run frontend validation if needed.

### Manual Verification
- Log in as a `tenant` and verify that the KYC page displays inputs, webcam stream, file upload, and signature pad.
- Log in as an `admin` and try to access `/kyc`. Verify that you are immediately redirected to `/admin/dashboard`.
- Verify that the Admin Dashboard loads and displays the audit grid, and that the CSV report scheduling triggers successfully.
- Search listings, click on an amenity in a property detail view, and verify that the map renders a line along the route.
- Open the Rental Agreement wizard and verify the 5 steps complete successfully.
