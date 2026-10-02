# Implementation Plan: Fix 502 Bad Gateway on Login

The 502 Bad Gateway is caused by a crash in the `auth_service` when it encounters an unrecognized password hash format in the database (PBKDF2 instead of the expected Bcrypt). This plan fixes the data inconsistency and hardens the auth service.

## User Review Required

> [!IMPORTANT]
> The current test users (e.g., `admin@rentora.com`) will have their passwords reset to the correctly hashed version of `password123` or their fixture defaults.

## Proposed Changes

### 1. Scripting & Data
- **[MODIFY] [scripts/seed_dev_all.py](file:///d:/Python%20Projects/Rentaro/scripts/seed_dev_all.py)**: Import `passlib.context.CryptContext` and use it to hash passwords correctly during seeding using the `bcrypt` algorithm.
- **[EXECUTE]** `python scripts/seed_dev_all.py` to refresh the `rentora_auth.db` with valid hashes.

### 2. Auth Service
- **[MODIFY] [auth_service/main.py](file:///d:/Python%20Projects/Rentaro/auth_service/main.py)**: Add a `try/catch` block around the `pwd_context.verify()` call to return a standard `401 Unauthorized` instead of crashing (500) if an invalid hash format is encountered in the future.

### 3. Frontend (As requested)
- **[MODIFY] [frontend/src/pages/Login.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/Login.tsx)**: Ensure the 502 error message is user-friendly and provides a "Retry" guidance (already partially implemented, will refine).

## Verification Plan

### Automated Verification
- Invoke the login endpoint via `curl` through the API Gateway (port 8000) and verify it returns 200 for correct credentials and 401 for incorrect ones, without crashing.

### Manual Verification
1. Open the application at `http://localhost:5173`.
2. Login as `admin@rentora.com`.
3. Verify successful entry to the Dashboard.
