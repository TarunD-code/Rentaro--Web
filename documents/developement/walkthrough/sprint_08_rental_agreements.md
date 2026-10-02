# Sprint 8: Walkthrough — Rental Agreements

## What Was Built
- Rental agreement model in property_service
- Agreement creation, viewing, and signing workflows
- Digital agreement signing with status transitions
- Agreement listing in tenant and owner dashboards

## Key Files
- `property_service/models.py` — RentalAgreement model
- `property_service/main.py` — Agreement endpoints
- `frontend/src/pages/AgreementWorkflow.tsx` — Agreement detail/signing

## Agreement Model
- **RentalAgreement**: property_id, tenant_id, owner_id, start_date, end_date, monthly_rent, security_deposit, terms, status
- **Status Flow**: draft → tenant_review → signed → active → expired/terminated

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/agreements` | Create agreement (owner) |
| GET | `/agreements/{id}` | Get details |
| GET | `/agreements` | List agreements |
| PUT | `/agreements/{id}/sign` | Tenant signs |
| PUT | `/agreements/{id}/status` | Update status |

## Dashboard Integration
- Tenant sees their agreements with status badges
- Owner sees agreements for their properties
- Click agreement → Full detail page with action buttons
