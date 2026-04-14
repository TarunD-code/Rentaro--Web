# Sprint 11: Walkthrough — Move-Out & Settlement

**Flag**: `epic6_sprint11_moveout_v1`

## What Was Built
Complete move-out lifecycle: tenant notice → owner review → deductions → settlement PDF → deposit refund → property auto-relist.

## Key Files Created
| File | Purpose |
|------|---------|
| `payment_service/settlement_pdf.py` | HTML-to-PDF branded settlement generator |
| `frontend/src/pages/MoveOutInitiate.tsx` | Notice period form + status stepper |
| `frontend/src/pages/MoveOutReview.tsx` | Owner deduction review with deposit bar |
| `frontend/src/pages/SettlementPage.tsx` | Settlement breakdown + PDF download |
| `frontend/src/components/MoveOutStatusCard.tsx` | Dashboard stepper widget |
| `payment_service/templates/moveout_initiated.html` | Owner notification email |
| `payment_service/templates/settlement_ready.html` | Settlement finalized email |
| `payment_service/templates/property_relisted.html` | Auto-relist email |
| `scripts/seed_moveout.py` | Seed (2 move-outs + 1 settlement) |
| `tests/test_moveout_service.py` | 17 tests |
| `frontend/cypress/e2e/sprint11_moveout.cy.ts` | E2E tests |

## Models Added (to payment_service)
- **MoveOutRequest**: status lifecycle: initiated → notice_period → owner_review → settlement_pending → completed
- **SettlementRecord**: deposit_amount, deductions (cleaning + damage + pending_rent + custom), refund_amount, PDF URL

## Modified Files
- `payment_service/models.py` — Added MoveOutStatus, SettlementStatus enums + 2 models
- `payment_service/schemas.py` — 6 new schemas
- `payment_service/main.py` — 7 new move-out endpoints
- `property_service/models.py` — Added status + available_from columns
- `property_service/main.py` — Added PUT /properties/{id}/status
- `TenantDashboard.tsx` — Move-out button + status card
- `OwnerDashboard.tsx` — Review alert + status card

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/payment/moveout/initiate` | Start 30-day notice |
| GET | `/payment/moveout/{id}` | Move-out details |
| GET | `/payment/moveout/active/me` | Active move-out |
| POST | `/payment/moveout/review` | Submit deductions |
| POST | `/payment/moveout/settlement` | Finalize + PDF |
| GET | `/payment/moveout/settlement/{id}` | Get settlement |
| GET | `/payment/moveout/settlement/{id}/html` | HTML view |

## Testing — 17/17 Passed
Enums (3) | Models (3) | Transitions (2) | Calculations (4) | PDF (3) | Flow (2)

## API Smoke Results
- Review: deposit 50k, deductions 9k, refund 41k ✅
- Settlement: finalized, PDF URL generated ✅
