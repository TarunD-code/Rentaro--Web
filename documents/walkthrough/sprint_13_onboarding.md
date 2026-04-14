# Sprint 13: Walkthrough — Tenant Onboarding & Digital Agreements

**Flag**: `epic7_sprint13_onboarding_v1` | **Port**: 8006

## What Was Built
New `onboarding_service` microservice handling the complete tenant onboarding lifecycle: personal details, KYC document upload and verification, digital rental agreement generation, and e-signatures.

## Key Files Created
| File | Purpose |
|------|---------|
| `onboarding_service/__init__.py` | Package init |
| `onboarding_service/database.py` | SQLite config |
| `onboarding_service/models.py` | OnboardingRecord, OnboardingKYC, DigitalAgreement, SignatureRecord |
| `onboarding_service/schemas.py` | Pydantic V2 schemas |
| `onboarding_service/main.py` | 15 API endpoints |
| `onboarding_service/agreement_pdf.py` | HTML agreement generator |
| `onboarding_service/tasks.py` | Celery-ready tasks |
| `onboarding_service/templates/onboarding_complete.html` | Onboarding verified email |
| `onboarding_service/templates/agreement_ready.html` | Agreement signing email |
| `onboarding_service/templates/signature_complete.html` | Fully signed email |
| `frontend/src/pages/OnboardingForm.tsx` | 3-step tenant onboarding |
| `frontend/src/pages/AgreementPage.tsx` | Agreement management & signing |
| `frontend/src/components/OnboardingStatusCard.tsx` | Dashboard widget |
| `scripts/seed_onboarding.py` | Seed data |
| `tests/test_onboarding_service.py` | 18 tests |
| `frontend/cypress/e2e/sprint13_onboarding.cy.ts` | E2E tests |

## Models
- **OnboardingRecord**: Tracks the tenant's move-in details and KYC lifecycle.
- **DigitalAgreement**: Stores lease terms, rent, deposit, notice period, and status.
- **SignatureRecord**: Tracks when the tenant and owner sign the agreement.

## Modified Files
- `gateway/main.py` — Added ONBOARDING_SERVICE_URL + route
- `start.bat` — Added onboarding service startup
- `App.tsx` — Added routes (`/onboarding/form`, `/onboarding/agreements`)
- `TenantDashboard.tsx` — Added OnboardingStatusCard
- `OwnerDashboard.tsx` — Added OnboardingStatusCard
- `featureFlags.ts` — Added epic7_sprint13_onboarding_v1

## Status Transitions
```
Onboarding: initiated → documents_pending → kyc_submitted → kyc_verified → completed
Agreement:  draft → generated → sent_for_signing → tenant_signed → owner_signed → fully_signed
```

## Testing — 15/15 Passed
- Enums (4) | Models (8) | Flow (3)

## API Smoke Results
- `GET /stats` → total=2, agreements=2, active=1 ✅
- `POST /agreements/create` → Created new agreement (generated) ✅
- `POST /agreements/sign` → Sent for signing (2 signers) ✅
- `POST /agreements/3/sign/tenant` → tenant_signed ✅
- `POST /agreements/3/sign/owner` → fully_signed ✅

## Seed Data
- 2 onboardings (1 completed, 1 pending KYC)
- 3 KYC docs (Aadhaar, PAN, Passport)
- 2 agreements (1 fully_signed, 1 pending_signatures)
