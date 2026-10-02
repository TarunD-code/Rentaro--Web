# Goal: Fix Authentication Persistence & In-Memory Store

The goal is to resolve the issue where user data is lost after a server restart, and to eliminate the use of in-memory dictionaries for critical auth flows.

## Analysis & Root Causes

1. **Database Pathing Issue (The "Lost User" Bug):**
   In `auth_service/database.py`, the SQLite connection string is `"sqlite:///./rentora_auth.db"`. This creates the DB in the *Current Working Directory (CWD)* of whoever launched the server. If a developer runs the server from `auth_service/` sometimes, and from the root directory other times, they will have two separate databases. This is why restarting the server seemingly deletes users!

2. **In-Memory OTP Store:**
   In `auth_service/main.py`, the OTPs generated during signup are stored in a python dictionary `OTP_STORE = {}`. If the server restarts before a user verifies their OTP, their OTP is permanently lost.

## Proposed Changes

### Database Configuration (auth_service/database.py)
- **[MODIFY]** Change the connection string to use an **absolute path** based on the root of the project, guaranteeing that the exact same database file is used regardless of where the server is launched from.

### Database Models (auth_service/models.py)
- **[MODIFY]** Add `otp_code = Column(String, nullable=True)` to the `User` model. This permanently replaces the in-memory array.

### Authentication Flow (auth_service/main.py)
- **[MODIFY]** Remove `OTP_STORE = {}`.
- **[MODIFY]** In `signup`: Save the generated OTP directly to `new_user.otp_code` and commit to the database. Add logging for success/failure.
- **[MODIFY]** In `verify_otp`: Query the user from the database and compare `db_user.otp_code` instead of checking the dictionary.
- **[MODIFY]** Add extensive debugging logs during Signup and Login to confirm database transactions are succeeding.

## Verification Plan

### Automated/Manual Verification
1. I will execute the backend services.
2. I will create a new user via the API (Signup).
3. I will kill the backend processes completely (Restart).
4. I will attempt to verify the OTP and login using the same credentials.
5. Success will be confirmed when login works and the "Invalid credentials" error is eliminated.
