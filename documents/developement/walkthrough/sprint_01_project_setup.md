# Sprint 1: Walkthrough — Project Setup & Auth Service

## What Was Built
- Bootstrapped the Rentora monorepo with Python backend (FastAPI) and React frontend (Vite)
- Created `auth_service` microservice on port 8001 with JWT authentication
- Created `gateway` reverse proxy on port 8000
- Set up `start.bat` for launching all services

## Key Files
- `auth_service/__init__.py`, `main.py`, `models.py`, `schemas.py`, `database.py`
- `gateway/__init__.py`, `main.py`
- `frontend/` — Vite + React + TypeScript scaffold
- `start.bat` — Multi-service launcher

## Auth Service Details
- **User Model**: email, hashed_password, role, is_verified, otp_code, otp_expires
- **Register**: Creates user with hashed password, generates 6-digit OTP
- **Login**: Validates credentials, returns JWT (sub=email, role, exp=24h)
- **Verify OTP**: Marks user as verified
- **Security**: bcrypt + PyJWT with `RENTORA_SUPER_SECRET_KEY`

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/verify-otp` | Verify email OTP |

## Frontend Pages
- `/register` — Registration form with role selector
- `/login` — Login form
- `/verify` — OTP input page

## Database
- `rentora_auth.db` (SQLite) — User table with auto-migration
