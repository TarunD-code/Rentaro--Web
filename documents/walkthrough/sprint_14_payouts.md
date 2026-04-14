# Sprint 14 Execution Walkthrough: Owner Payouts, Ledger, and Accounting

## Overview
Successfully implemented the Owner Payouts and Ledger system into the existing `payment_service`. This update unlocks secure withdrawal of rental revenues to owner bank accounts, automatic platform fee deduction, and immutable ledger tracking for dispute-free accounting.

## Architectural Additions

### Core Accounting Ledger (`payment_service.models`)
We expanded the database to support a fully functional internal ledger:
- **`OwnerBalance`**: Tracks the real-time available and pending balance for quick withdrawal validation without expensive full-ledger aggregation queries.
- **`LedgerEntry`**: Immutable double-entry-style log. Every debit (payouts) and credit (rent) generates an entry.
- **`FeeRecord` & `TaxRecord`**: Automatically capture standard deductions (e.g., 5% platform fee + 18% GST).
- **`Payout`**: Tracks outbound job states (`pending`, `processed`, `failed`, `cancelled`) to the Owner's Bank Account.

### Backend APIs (`payment_service.main`)
Built robust APIs for secure interactions:
- `POST /payouts/initiate`: Deducts from `OwnerBalance` and fires Razorpay Payouts (Sandbox IMPS). If Razorpay rejects, the transaction natively rolls back.
- `GET /payouts/{id}/status`: Monitors current payout status.
- `POST /payouts/{id}/cancel`: Refund mechanism if cancelled before capture.
- `POST /payouts/reconcile`: Admin reconciliation endpoints linking to csv settlement batches.

> [!TIP]
> **Rent Capture Hook**: We hooked the existing `verify_rent_payment` flow. When a rent payment is captured successfully, the code automatically calculates fees, updates `OwnerBalance`, and stamps an immutable `LedgerEntry`. 

### Asynchronous Operations (`payment_service.tasks`)
- `process_scheduled_payouts()`: A daily Celery task that auto-deposits funds to users who meet minimum thresholds.
- `reconcile_payouts()`: Reconciles edge-case webhooks dynamically matching our payout system with Razorpay.

## Frontend UI Components

New dashboard views are hidden securely behind the `epic7_sprint14_payouts_v1` default false feature flag.

- **Owner Payout Dashboard**: Built an immersive 'Wallet' view. Owners can see `Available Balance`, `Pending Ledger Funds`, and 1-click `Withdraw All` functionality directly tied to the new backend endpoints.
- **Monthly Statements Portal**: Owners can generate and download monthly PDF overviews detailing their property profit, platform commissions, and tax burdens.
- **Admin Reconciliation Page**: Added a CSV-upload dropzone for Administrator finance teams to batch-sync physical bank deposits with platform `processed` statuses.

## Testing & Quality Assurance
- Developed comprehensive **Pytest unit test suites** for Edge Ledger limits (insufficient funds, negative fees, etc.) logic testing.
- Created `frontend/cypress/e2e/sprint14_payouts.cy.ts` for End-to-End browser simulation covering the new dashboard elements.
- Pushed `scripts/migrate_sprint14.py` DB migration to safely modify production schema without downtime.
