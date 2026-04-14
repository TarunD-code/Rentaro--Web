# Sprint 13: Implementation Plan — Tenant Onboarding & Digital Agreements

**Date**: April 14, 2026 | **Flag**: `epic7_sprint13_onboarding_v1`

## Goal
Implement tenant onboarding workflows, digital rental agreement generation, e-signatures, and KYC verification.

## Architecture Decisions
- New `onboarding_service` microservice on port 8006, isolated `rentora_onboarding.db`
- Move-in domain logic centralized here (tenant details, KYC, agreement PDF, e-signatures)
- Fallback HTML to PDF via WeasyPrint integration logic (provided via HTML response for now)
- DocuSign stub logic via signature tracking tables

## Proposed Changes

### 1. New Microservice — `onboarding_service/` (Port 8006)
- `database.py` — SQLAlchemy engine → `rentora_onboarding.db`
- `models.py`:
  - **OnboardingRecord**: tenant details, emergency contact, employer, status lifecycle (initiated → documents_pending → kyc_submitted → kyc_verified → completed)
  - **OnboardingKYC**: Document type, number, file URL, status
  - **DigitalAgreement**: Agreement terms, status (draft → generated → sent_for_signing → tenant_signed → owner_signed → fully_signed → active)
  - **SignatureRecord**: Signer tracking
- `schemas.py` — Pydantic V2 schemas
- `main.py` — 15 API endpoints
- `tasks.py` — Async task stubs
- `agreement_pdf.py` — HTML agreement generator

### 2. API Design (15 endpoints)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/onboarding/initiate` | Start onboarding |
| GET | `/onboarding/{id}` | Get onboarding |
| GET | `/onboarding/active/me` | Active onboarding |
| PUT | `/onboarding/{id}/status` | Update status |
| POST | `/onboarding/kyc` | Upload KYC |
| GET | `/onboarding/{id}/kyc` | List KYC |
| PUT | `/onboarding/kyc/{id}/verify` | Admin verify KYC |
| POST | `/agreements/create` | Create agreement |
| GET | `/agreements` | List agreements |
| GET | `/agreements/{id}/pdf` | Agreement PDF |
| POST | `/agreements/sign` | Send for signing |
| POST | `/agreements/{id}/sign/{role}`| Sign contract |
| GET | `/stats` | Onboarding stats |

### 3. Frontend Pages
- `OnboardingForm.tsx`: Personal Details, KYC upload, Review
- `AgreementPage.tsx`: Listing, creating, sending, and signing agreements
- `OnboardingStatusCard.tsx`: Dashboard widget for pending KYC and signatures

### 4. Infrastructure
- Gateway: `onboarding/*` → port 8006
- `start.bat` updated with port 8006
- Email templates: `onboarding_complete.html`, `agreement_ready.html`, `signature_complete.html`

## Verification
- 18 backend tests
- API smoke tests for signature flow
- Cypress E2E tests for onboarding Form and Agreement list
