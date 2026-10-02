# Sprint 2: Implementation Plan — Profile Service & Dashboard

## Goal
Implement user profile management with KYC document upload and role-based dashboard.

## Proposed Changes

### 1. Profile Service (Port 8002)
- **Database**: `rentora_profile.db` (SQLite)
- **Models**: `UserProfile` — email, full_name, phone, bio, avatar_url, address, kyc_status, kyc_documents
- **Endpoints**:
  - `GET /profile/{email}` — Get user profile
  - `PUT /profile/{email}` — Update profile
  - `POST /profile/upload-avatar` — Upload avatar image
  - `POST /profile/upload-kyc` — Upload KYC documents
- **Storage**: Local file storage in `uploads/` directory

### 2. Dashboard Page
- Role-based rendering (tenant vs owner vs admin)
- Profile summary card with avatar
- Quick action buttons

### 3. Gateway Update
- Add `PROFILE_SERVICE_URL` and routing for `profile/*`

## Verification
- Create profile → Upload avatar → Update details → View on dashboard
