# Sprint 1: Implementation Plan — Project Setup & Auth Service

## Goal
Bootstrap the Rentora platform with project structure, development environment, and user authentication.

## Proposed Changes

### 1. Project Structure
- Initialize Python virtual environment with FastAPI, SQLAlchemy, PyJWT
- Create `auth_service/` package with modular structure
- Initialize Vite + React + TypeScript frontend
- Setup `.gitignore`, `start.bat`

### 2. Auth Service (Port 8001)
- **Database**: `rentora_auth.db` (SQLite)
- **Models**: `User` — email, hashed_password, role (tenant/owner/admin), is_verified, otp_code, otp_expires
- **Endpoints**:
  - `POST /auth/register` — Register with email, password, role
  - `POST /auth/login` — Login with JWT token generation
  - `POST /auth/verify-otp` — OTP-based email verification
- **Security**: bcrypt password hashing, JWT tokens with 24h expiry, OTP with 10-min expiry

### 3. API Gateway (Port 8000)
- FastAPI reverse proxy using httpx
- CORS configuration for frontend
- Route prefix stripping for service isolation

### 4. Frontend Foundation
- Vite + React + TypeScript + MUI setup
- Pages: Register, Login, VerifyOTP
- Basic routing with React Router v6

## Verification
- Register a user → Receive OTP → Verify → Login → Get JWT token
