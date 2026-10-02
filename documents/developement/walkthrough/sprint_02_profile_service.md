# Sprint 2: Walkthrough — Profile Service & Dashboard

## What Was Built
- Created `profile_service` microservice on port 8002
- User profile CRUD with avatar and KYC document upload
- Role-based Dashboard page with profile summary
- KYCStepper component for document verification workflow

## Key Files
- `profile_service/main.py`, `models.py`, `schemas.py`, `database.py`, `storage.py`
- `frontend/src/pages/Dashboard.tsx`, `Profile.tsx`
- `frontend/src/components/KYCStepper.tsx`, `RoleSelector.tsx`

## Profile Service Details
- **UserProfile Model**: email, full_name, phone, bio, avatar_url, address, kyc_status (pending/submitted/verified/rejected), kyc_documents (JSON)
- **Storage**: File-based storage in `uploads/` with `profile_service/storage.py` handling file operations
- **KYC Flow**: Upload documents → Status: submitted → Admin reviews → verified/rejected

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile/{email}` | Get profile |
| PUT | `/profile/{email}` | Update profile |
| POST | `/profile/upload-avatar` | Upload avatar |
| POST | `/profile/upload-kyc` | Upload KYC docs |

## Dashboard
- Shows role-specific content (tenant sees applications, owner sees properties)
- Profile card with avatar, name, role badge
- Quick action navigation cards

## Database
- `rentora_profile.db` (SQLite) — UserProfile table
