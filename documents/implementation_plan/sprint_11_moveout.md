# Sprint 11: Implementation Plan — Move-Out & Settlement

**Date**: April 13, 2026 | **Flag**: `epic6_sprint11_moveout_v1`

## Goal
Implement complete move-out lifecycle: tenant notice → owner review → deposit deductions → settlement PDF → refund → property auto-relist.

## Architecture Decisions
- Move-out logic centralized in `payment_service` (financial workflow)
- Cross-service HTTP call to `property_service` for auto-relisting
- Settlement PDF via WeasyPrint with HTML fallback
- 30-day default notice period

## Proposed Changes

### 1. New Models (payment_service)
- **MoveOutRequest**: agreement_id, property_id, tenant/owner_id, status (initiated→notice_period→owner_review→settlement_pending→completed→cancelled), notice_period_days, reason, expected/actual_vacate_date
- **SettlementRecord**: deposit_amount, pending_rent, cleaning_charge, damage_charge, total_deductions, refund_amount, deductions_json, settlement_pdf_url, status (draft→finalized→paid)
- Enums: `MoveOutStatus`, `SettlementStatus`, `TransactionType.settlement`

### 2. Move-Out Endpoints (payment_service)
- `POST /moveout/initiate` — 30-day notice
- `GET /moveout/{id}`, `GET /moveout/active/me`
- `POST /moveout/review` — Owner submits deductions
- `POST /moveout/settlement` — Finalize + PDF + relist
- `GET /moveout/settlement/{id}`, `/settlement/{id}/html`

### 3. Property Service Update
- Add `status` (available/occupied/maintenance/unlisted) and `available_from` to Property
- `PUT /properties/{id}/status` endpoint

### 4. Settlement PDF Generator
- Branded HTML template with deductions breakdown
- WeasyPrint PDF with HTML fallback

### 5. Frontend Pages
- MoveOutInitiate: Notice form + status stepper
- MoveOutReview: Deposit bar, deduction form, "No Deductions" action
- SettlementPage: Breakdown + PDF download
- MoveOutStatusCard: Dashboard widget with urgency countdown

### 6. Deduction Logic
```
total_deductions = pending_rent + cleaning_charge + damage_charge + sum(custom_deductions)
refund_amount = max(0, deposit_amount - total_deductions)
```

## Verification
- 17 backend tests (enums, models, transitions, calculations, PDF, flow)
- API smoke tests for all endpoints
