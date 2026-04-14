# Sprint 14 Deploy Notes

## Database Migration
Must be executed BEFORE enabling feature flags on frontend.
```bash
python scripts/migrate_sprint14.py
```
*Creates: `OwnerBalance`, `LedgerEntries`, `Payouts`, `FeeRecords`, `TaxRecords`*

## Configuration Flags 
### Frontend (`featureFlags.ts`)
Set `epic7_sprint14_payouts_v1 = true` to reveal Wallet / Statements module.

## Environment Variables
The `payment_service` requires standard Razorpay Sandbox credentials. No new ENV vars were strictly added since Razorpay IMPS payouts run via the existing API KEY.

However, Celery must be running to process auto-payouts natively:
```bash
celery -A payment_service.tasks worker --loglevel=info
```
