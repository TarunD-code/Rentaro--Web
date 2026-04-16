# Implementation Plan - Sprint 14 CI Stabilization (feature/sprint14)

Stabilize the `feature/sprint14` branch by resolving all TypeScript compilation errors (`TS6133`, `TS2769`) and ensuring the CI pipeline is compatible with Node.js 24.

## Proposed Changes

### 1. CI Workflow Update
#### [MODIFY] .github/workflows/ci.yml
- Update `node-version` to `24`.
- Add `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` to environment variables.
- Update `actions/setup-python` to `v5`.

---

### 2. Frontend Type & Import Cleanup
#### [MODIFY] Multiple Files
Remove unused imports and variables flagged by `TS6133` in:
- `OnboardingStatusCard.tsx`, `RentReminderCard.tsx`, `AgreementPage.tsx`, `Listings.tsx`, `Login.tsx`, `MaintenanceHistory.tsx`, `MoveOutInitiate.tsx`, `MoveOutReview.tsx`, `OnboardingForm.tsx`, `OwnerAssignmentPanel.tsx`, `OwnerPayoutDashboard.tsx`, `PaymentHistory.tsx`, `ServiceRequestForm.tsx`, `SettlementPage.tsx`, `StatementsPage.tsx`, `VendorTaskView.tsx`.

#### [MODIFY] [OwnerPayoutDashboard.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/OwnerPayoutDashboard.tsx)
#### [MODIFY] [StatementsPage.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/StatementsPage.tsx)
- Transition `Grid` items from legacy `item` prop to the modern `size` prop (MUI v2) to resolve `TS2769` "No overload matches this call" errors.

---

### 3. Verification Plan
- Run `npm run lint -- --fix` in `frontend/`.
- Run `npx tsc -b` in `frontend/` to confirm zero compilation errors.
- Run `npm run build` to ensure the logic and types are fully valid.

## Open Questions
- None. The task is well-defined and based on previously verified successful remediation on the payouts branch.
