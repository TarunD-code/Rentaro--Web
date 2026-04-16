# Sprint 14: Implementation Plan — Owner Payouts, Settlements & Accounting

**Date**: April 14, 2026 | **Flag**: `epic7_sprint14_payouts_v1`

## Goal
Implement a robust ledger, payout integration, and monthly statement generation engine for property owners.

## Architecture Decisions
To maintain atomic consistency when rent transitions from `captured` to owner account boundaries, this feature set will safely extend the existing **`payment_service`** (Port 8004) rather than building a siloed accounting microservice. This guarantees atomic Ledger balancing without managing edge-case two-phase microservice failures over HTTP.

## Proposed Changes

### 1. Database & Models (`payment_service/models.py`)
Add the following core accounting models to the schema:
- **`OwnerBalance`**: Aggregated running total available to an owner.
- **`LedgerEntry`**: Immutable record of all money movement (Rent, Fee, Tax, Payout).
- **`FeeRecord` / `TaxRecord`**: Platform fees (e.g., standard 5% cut) and associated compliance taxes.
- **`Payout`**: Batch request sending funds to an owner's bank account (tracking Razorpay Payout ID).

### 2. Microservice API & Gateway (`payment_service/main.py`)
Add accounting and payout specific routes. We will also update `gateway/main.py` to route `/payouts`, `/owners`, and `/ledger` to `PAYMENT_SERVICE_URL`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payouts/initiate` | Manually request/trigger a payout batch |
| GET | `/payouts/{id}/status` | Poll payout execution status |
| POST | `/payouts/{id}/cancel` | Attempt to cancel pending payout |
| POST | `/payouts/reconcile` | Upload bank CSV/Callback resolver |
| GET | `/owners/{id}/statements` | Download CSV/PDF monthly statements |

### 3. Asynchronous Tasks (`payment_service/tasks.py`)
Leverage the Celery pipeline config (`docker-compose.celery.yml`):
- `process_scheduled_payouts()`: Cron job running daily to batch auto-clear unlocked balances.
- `generate_monthly_statements()`: Renders WeasyPrint PDFs and emails them securely via SendGrid.
- `reconcile_payouts()`: Checks Razorpay standard T+1 settlements vs actual ledger expectation.

### 4. Statement Generation (`payment_service/statement_pdf.py`)
- WeasyPrint template `owner_statement.html` aggregating Ledger Entries of a given month into a professional financial document (with CSV backup).

### 5. Frontend UI
- `frontend/src/pages/OwnerPayoutDashboard.tsx`: Owner-exclusive interface showing balances, payout requests, and ledger breakdown.
- `frontend/src/pages/StatementsPage.tsx`: Download grid for monthly summaries.
- `frontend/src/pages/ReconciliationAdmin.tsx`: Admin interface for managing mismatched ledger reports.

## Open Questions
- **Platform Fee %**: Assuming a flat 5% deduction for now unless specified otherwise.
- **Payout Webhooks**: We will add the Razorpay Payout webhook router (`payout.processed`, `payout.reversed`) into the existing `webhook/razorpay` endpoint.

## Verification Plan

### Automated Tests
- Unit testing checking `OwnerBalance` integrity updates against positive/negative entries.
- DB constraint tests against `LedgerEntry` mutations.
- Cypress E2E running `sprint14_payouts.cy.ts` proving Owner sees zero balance, rent is paid by tenant, balance shifts, and owner processes manual withdrawal.

### Manual Steps
- Check `.env.example` placeholder populations.
- Run `verify_login.py` helper to ensure admin tokens work against `/owners/{id}/statements` protected route mapping.
