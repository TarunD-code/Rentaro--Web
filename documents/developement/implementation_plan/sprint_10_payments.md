# Sprint 10: Implementation Plan — Payment System

**Date**: April 9, 2026 | **Flag**: `epic5_sprint10_payments_v1`

## Goal
Implement secure end-to-end payment lifecycle: deposit collection, monthly rent billing, auto-pay mandates, and transaction history.

## Architecture Decision
- New `payment_service` microservice on port 8004, isolated database (`rentora_payments.db`)
- Razorpay integration with full sandbox/mock mode for development
- All payment logic centralized — no cross-service DB access

## Proposed Changes

### 1. Payment Service (Port 8004)
- **Database**: `rentora_payments.db` (SQLite)
- **Models**:
  - `PaymentTransaction` — agreement_id, tenant_id, owner_id, property_id, transaction_type, amount, razorpay_order_id/payment_id/signature, status, paid_at
  - `AutoPayMandate` — tenant_id, agreement_id, razorpay_subscription_id, status, max_amount, frequency, next_charge_date
- **Endpoints**:
  - `POST /create-order` — Create Razorpay order
  - `POST /verify` — Verify payment signature
  - `GET /transactions` — List user transactions
  - `POST /mandate/create` — Create auto-pay mandate
  - `GET /mandate/status` — Get mandate status
  - `POST /mandate/charge` — Charge via mandate
  - `GET /receipt/{txn_id}` — Get payment receipt

### 2. Razorpay Client
- Abstraction layer with sandbox mode
- Mock client for development (no real API calls)
- Production-ready client with order/payment APIs

### 3. Frontend Pages
- `DepositPayment.tsx` — Deposit capture with progress bar
- `AutoPaySetup.tsx` — Mandate creation wizard
- `PaymentHistory.tsx` — Transaction table with filters
- `RentReminderCard.tsx` — Dashboard reminder widget

### 4. Infrastructure
- Gateway routing for `payment/*`
- `start.bat` updated with payment service
- Email templates: deposit receipt, payment confirmation, mandate setup

## Verification
- 21 backend integration tests
- Cypress E2E tests for full payment flow
- API smoke tests for all 7 endpoints
