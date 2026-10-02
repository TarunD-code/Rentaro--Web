# Sprint 10: Walkthrough — Payment System

**Flag**: `epic5_sprint10_payments_v1` | **Port**: 8004

## What Was Built
Complete payment lifecycle: deposit collection, monthly rent billing, auto-pay mandates, and transaction history with Razorpay integration.

## Key Files Created
| File | Purpose |
|------|---------|
| `payment_service/main.py` | Payment API with Razorpay integration |
| `payment_service/models.py` | PaymentTransaction, AutoPayMandate models |
| `payment_service/schemas.py` | Pydantic schemas |
| `payment_service/database.py` | SQLite config |
| `payment_service/razorpay_client.py` | Razorpay abstraction (sandbox + prod) |
| `payment_service/tasks.py` | Celery-ready payment tasks |
| `payment_service/notifications.py` | Email/SMS dispatchers |
| `frontend/src/pages/DepositPayment.tsx` | Deposit payment page |
| `frontend/src/pages/AutoPaySetup.tsx` | Auto-pay mandate setup |
| `frontend/src/pages/PaymentHistory.tsx` | Transaction history table |
| `frontend/src/components/RentReminderCard.tsx` | Dashboard reminder widget |
| `scripts/seed_payments.py` | Seed data script |
| `tests/test_payment_service.py` | 21 integration tests |

## Models
- **PaymentTransaction**: transaction_type (deposit/rent/settlement/refund), payment_method, amount, razorpay_order_id/payment_id/signature, status (created/authorized/captured/failed/refunded), paid_at
- **AutoPayMandate**: razorpay_subscription_id, status (created/authenticated/active/paused/cancelled/expired), max_amount, frequency, next_charge_date

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/create-order` | Create Razorpay order |
| POST | `/verify` | Verify payment |
| GET | `/transactions` | Transaction history |
| POST | `/mandate/create` | Create auto-pay |
| GET | `/mandate/status` | Mandate status |
| POST | `/mandate/charge` | Charge mandate |
| GET | `/receipt/{id}` | Payment receipt |

## Testing
- **21 backend tests** — all passing
- Cypress E2E tests

## Dashboard Integration
- RentReminderCard widget on TenantDashboard
- Quick action buttons for deposit and history
