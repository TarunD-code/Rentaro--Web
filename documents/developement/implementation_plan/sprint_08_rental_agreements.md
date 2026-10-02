# Sprint 8: Implementation Plan — Rental Agreements

## Goal
Implement rental agreement creation, digital signing workflow, and agreement management.

## Proposed Changes

### 1. Agreement Model (Property Service)
- **RentalAgreement**: property_id, tenant_id, owner_id, start_date, end_date, monthly_rent, security_deposit, terms, status (draft/tenant_review/signed/active/expired/terminated)

### 2. Agreement Endpoints
- `POST /agreements` — Owner creates agreement
- `GET /agreements/{id}` — Get agreement details
- `GET /agreements` — List user agreements (role-based)
- `PUT /agreements/{id}/sign` — Tenant signs agreement
- `PUT /agreements/{id}/status` — Update agreement status

### 3. Frontend
- Agreement creation form (owner)
- Agreement detail page with status workflow
- Agreement signing flow (tenant)
- Agreement listing in dashboard

## Verification
- Owner creates agreement → Tenant reviews → Tenant signs → Status: active
