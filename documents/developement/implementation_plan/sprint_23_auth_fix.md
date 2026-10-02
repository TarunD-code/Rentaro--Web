# Implementation Plan - Fix Persistent Login 401 Errors

Users are seeing a misleading "Invalid credentials or internal hash mismatch" error during login. This is caused by a bug in the `auth_service` where a broad `exception` handler catches intentional `HTTPException` (raised for invalid credentials) and transforms it into a generic "hash mismatch" error. Additionally, a typo in the seeded user's email (`rentora` vs `rentaro`) is a common cause for initial login failures.

## User Review Required

> [!IMPORTANT]
> **Typo in Credentials**: The seeded administrator's email is `admin@rentora.com`. The screenshot provided shows an attempt with `admin@rentaro.com`. While the code fix will make the error message accurate ("Invalid credentials"), the user must use the correct spelling to log in successfully.

## Proposed Changes

### [Component] Authentication Service (`auth_service`)

#### [MODIFY] [main.py](file:///d:/Python%20Projects/Rentaro/auth_service/main.py)
- **Refactor Login Handler**: Move the database user check outside the hashing `try...except` block or ensure `HTTPException` is not caught by the broad handler.
- **Defensive Logging**: Add logging for "User not found" vs "Password mismatch" to differentiate errors in the server logs without leaking them to the client.
- **Specific Error Handling**: Catch specific hashing errors (if any) rather than a generic `Exception`.

---

### [Component] Database Seeding

#### [MODIFY] [fixtures.json](file:///d:/Python%20Projects/Rentaro/scripts/fixtures.json)
- Consider adding an alias or changing `rentora.com` to `rentaro.com` if that is the intended project naming, or simply ensure documentation reflects the current fixtures. I will proceed by keeping `rentora.com` as it is consistent across other services.

## Verification Plan

### Automated Tests
- Run `pytest d:\Python Projects\Rentaro\tests\test_auth.py` (if exists) or create a targeted test script to verify:
    - Login with correct credentials returns `200 OK`.
    - Login with non-existent user returns `401 Unauthorized` with "Invalid credentials".
    - Login with wrong password returns `401 Unauthorized` with "Invalid credentials".

### Manual Verification
- Perform a manual login in the browser with `admin@rentora.com` and `password123`.
- Intentionally use a wrong email and verify the error message is "Invalid credentials" (not the internal hash mismatch one).
