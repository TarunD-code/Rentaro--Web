# Requirements Document

## Introduction

The Rentora MVP platform consists of 12+ FastAPI microservices and a React/TypeScript frontend. A codebase audit has identified three categories of security vulnerabilities that must be remediated before production launch:

1. **Insecure Direct Object Reference (IDOR)**: Several services expose database-ID-parameterised endpoints that do not validate whether the authenticated caller owns or is party to the referenced resource. An attacker with a valid session can enumerate and access another user's agreements, maintenance requests, payment mandates, move-out records, and onboarding data by simply incrementing the ID.

2. **Missing Rate Limiting**: Only `auth_service` and `property_service` apply Redis-backed rate limits. The remaining services, including billing and payment endpoints, have no throttling.

3. **Insecure Session & Transport Configuration**: Ten services use `allow_origins=["*"]` in their CORS middleware. Ten services embed the JWT secret as a hardcoded string literal rather than reading it from the environment. Eight services are missing HTTP security headers entirely.

This feature delivers a hardening layer covering all three areas across the full service estate.

---

## Glossary

- **IDOR (Insecure Direct Object Reference)**: A vulnerability where a caller can access any resource by guessing or enumerating its database ID because the server does not confirm the caller is authorised for that specific record.
- **Ownership Check**: A server-side assertion that the authenticated caller's identity matches the `owner_id`, `tenant_id`, `actor_id`, or equivalent field on the database record before returning or modifying it.
- **Party Check**: An ownership check that accepts either of two principals (e.g., `tenant_id` OR `owner_id`) as authorised, used when both parties to a contract have legitimate read access.
- **Rate Limiter**: The shared `shared_rate_limiter.rate_limit` FastAPI dependency that enforces a sliding-window request quota per IP or per authenticated user, backed by Redis.
- **Security Headers Middleware**: A FastAPI `@app.middleware("http")` function that appends `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, and — in production — `Strict-Transport-Security` to every HTTP response.
- **CORS Middleware**: The `fastapi.middleware.cors.CORSMiddleware` configuration that controls which browser origins may make cross-origin requests to the service.
- **Allowed Origins**: The explicit list of frontend domains (`https://rentora.in`, `https://www.rentora.in`, `https://app.rentora.in` in production; `http://localhost:5173` and two local-network equivalents in development) that CORS permits.
- **JWT Secret**: The signing key used to issue and verify JSON Web Tokens. MUST be read from the `JWT_SECRET_KEY` environment variable at service startup; MUST NOT be embedded as a string literal in source code.
- **In-Memory Token Store**: The React module-level variables (`_accessToken`, `_role`) in `AuthContext.tsx` that hold the short-lived access token, inaccessible to XSS payloads.
- **HttpOnly Refresh Token**: A long-lived token stored in a cookie with the `HttpOnly; Secure; SameSite=Strict` attributes, making it inaccessible to JavaScript and automatically sent to the server on every qualifying request.
- **CSP (Content Security Policy)**: An HTTP response header that restricts which scripts, styles, and other resources a browser may load for a given page.
- **HSTS (HTTP Strict Transport Security)**: An HTTP response header that instructs browsers to contact the domain exclusively over HTTPS for a defined period.
- **Services Under Scope**: `agreements_service`, `billing_service`, `maintenance_service`, `notification_service`, `onboarding_service`, `owner_dashboard_service`, `payment_service`, `profile_service`, `search_service`, `subscription_service`, `support_service`, `geo_amenity_service`. (`auth_service` and `property_service` are already partially hardened and are in scope only for gaps.)
- **Admin Bypass**: A pattern where a caller with `role == "admin"` is granted access to any resource without an ownership check, used intentionally for administrative tooling.

---

## Requirements

### Requirement 1: IDOR Prevention — Agreements Service

**User Story:** As a security engineer, I want every endpoint in `agreements_service` that retrieves or mutates a specific agreement to verify the caller is a party to that agreement, so that tenants and owners cannot access each other's contract data.

#### Acceptance Criteria

1. WHEN a caller requests `GET /{id}` on the Agreements_Service, THE Agreements_Service SHALL verify that the caller's authenticated identity matches `agreement.owner_id` OR `agreement.tenant_id` before returning the record.
2. IF the authenticated caller is neither the owner nor the tenant of the requested agreement AND the caller's role is not `admin`, THEN THE Agreements_Service SHALL return HTTP 403 Forbidden.
3. WHEN a caller requests `POST /draft`, THE Agreements_Service SHALL require a valid JWT and verify that the `owner_id` field in the request body matches the authenticated caller's identity before creating the draft.
4. WHEN a caller requests `POST /{id}/generate-basic`, THE Agreements_Service SHALL require a valid JWT and verify that the authenticated caller is the `owner_id` of agreement `{id}` before generating the PDF.
5. IF the JWT is absent or invalid on any protected endpoint of the Agreements_Service, THEN THE Agreements_Service SHALL return HTTP 401 Unauthorized.

---

### Requirement 2: IDOR Prevention — Maintenance Service

**User Story:** As a security engineer, I want `GET /request/{request_id}` in `maintenance_service` to enforce ownership, so that tenants cannot read each other's maintenance tickets.

#### Acceptance Criteria

1. WHEN a caller requests `GET /request/{request_id}` on the Maintenance_Service, THE Maintenance_Service SHALL verify that the authenticated caller's identity matches `request.tenant_id` OR `request.owner_id` before returning the record.
2. IF the authenticated caller is not the submitting tenant, the responsible owner, or an admin, THEN THE Maintenance_Service SHALL return HTTP 403 Forbidden.
3. THE Maintenance_Service SHALL apply the same party check to `PATCH /request/{request_id}` and any other endpoint that retrieves or mutates a single maintenance request by ID.

---

### Requirement 3: IDOR Prevention — Payment Service

**User Story:** As a security engineer, I want financial endpoints in `payment_service` to enforce that callers can only access their own payment records, so that a malicious tenant cannot read another tenant's auto-pay mandate, move-out record, or settlement.

#### Acceptance Criteria

1. WHEN a caller requests `GET /autopay/status/{mandate_id}` on the Payment_Service, THE Payment_Service SHALL verify that `mandate.tenant_id` matches the authenticated caller's identity before returning the mandate.
2. IF the caller is not the mandate owner and not an admin, THEN THE Payment_Service SHALL return HTTP 403 Forbidden for the mandate status endpoint.
3. WHEN a caller requests `GET /moveout/{moveout_id}`, THE Payment_Service SHALL verify that the authenticated caller's identity matches `moveout.tenant_id` OR `moveout.owner_id`.
4. IF the caller is not a party to the move-out and not an admin, THEN THE Payment_Service SHALL return HTTP 403 Forbidden for the move-out detail endpoint.
5. WHEN a caller requests `GET /moveout/settlement/{settlement_id}`, THE Payment_Service SHALL verify that the authenticated caller's identity matches `settlement.tenant_id` OR `settlement.owner_id`.
6. IF the caller is not a party to the settlement and not an admin, THEN THE Payment_Service SHALL return HTTP 403 Forbidden for the settlement detail endpoint.
7. THE Admin_Bypass SHALL be honoured: WHEN the caller's role is `admin`, THE Payment_Service SHALL grant access without an ownership check.

---

### Requirement 4: IDOR Prevention — Onboarding Service

**User Story:** As a security engineer, I want `GET /onboarding/{onboarding_id}` and `PUT /onboarding/{onboarding_id}/status` in `onboarding_service` to validate the caller is the tenant or an admin, so that one tenant cannot view or modify another tenant's onboarding record.

#### Acceptance Criteria

1. WHEN a caller requests `GET /onboarding/{onboarding_id}` on the Onboarding_Service, THE Onboarding_Service SHALL verify that `record.tenant_id` matches the authenticated caller's identity OR the caller's role is `admin`.
2. IF the caller is not the record's tenant and not an admin, THEN THE Onboarding_Service SHALL return HTTP 403 Forbidden.
3. WHEN a caller requests `PUT /onboarding/{onboarding_id}/status`, THE Onboarding_Service SHALL verify that the caller is an admin before allowing status mutation.
4. IF a non-admin caller attempts `PUT /onboarding/{onboarding_id}/status`, THEN THE Onboarding_Service SHALL return HTTP 403 Forbidden.

---

### Requirement 5: IDOR Prevention — General Platform Rule

**User Story:** As a security engineer, I want a documented and enforceable rule that all future endpoints taking a database ID apply an ownership or party check, so that IDOR vulnerabilities do not reappear as new services are developed.

#### Acceptance Criteria

1. THE Platform SHALL enforce that every GET, PUT, PATCH, and DELETE endpoint that accepts a path parameter resolving to a database row includes an ownership or party check before returning or mutating data.
2. WHEN an ownership or party check fails on any service, THE service SHALL return HTTP 403 Forbidden with the detail `"You do not have permission to access this resource."`.
3. WHERE Admin_Bypass applies, THE service SHALL grant access only when `user_info["role"] == "admin"` is confirmed from the decoded JWT, not from a request parameter.
4. THE Platform SHALL not use HTTP 404 to mask the existence of a resource when the real reason for rejection is insufficient permission; HTTP 403 SHALL be used instead.

---

### Requirement 6: Rate Limiting — Authentication Endpoints

**User Story:** As a security engineer, I want strict rate limits on all authentication endpoints so that automated credential-stuffing, brute-force, and OTP-enumeration attacks are blocked at the application layer.

#### Acceptance Criteria

1. WHEN a caller submits `POST /auth/login` more than 5 times within any 60-second window from the same IP address, THE Auth_Service SHALL return HTTP 429 Too Many Requests with a `Retry-After` header set to 60.
2. WHEN a caller submits `POST /auth/signup` more than 3 times within any 300-second window from the same IP address, THE Auth_Service SHALL return HTTP 429 Too Many Requests with a `Retry-After` header set to 300.
3. WHEN a caller requests OTP generation (included in `/auth/signup` and `/auth/verify-otp`) more than 3 times within any 300-second window from the same IP address, THE Auth_Service SHALL return HTTP 429 Too Many Requests.
4. THE Rate_Limiter SHALL use the `X-Forwarded-For` header to determine client IP when the request passes through the API gateway, falling back to `request.client.host` when no forwarding header is present.
5. IF Redis is unavailable, THEN THE Auth_Service SHALL allow the request to proceed and SHALL log a warning, so that a Redis outage does not block legitimate user logins.

*Note: Requirements 6.1–6.3 are already implemented in `auth_service/main.py`. These criteria formally document the existing behaviour and require verification against the current implementation.*

---

### Requirement 7: Rate Limiting — Booking and Contact Endpoints

**User Story:** As a security engineer, I want rate limits on visit-booking and contact-host endpoints so that spam bots cannot flood property owners with fake booking requests.

#### Acceptance Criteria

1. WHEN an authenticated user submits `POST /visits` (book-visit) more than 10 times within any 3600-second window, THE Property_Service SHALL return HTTP 429 Too Many Requests with a `Retry-After` header set to 3600.
2. THE Rate_Limiter SHALL key the visit-booking limit on the authenticated user's JWT `sub` claim, not on IP address, so that shared-IP environments (NAT, VPN) do not penalise legitimate users.
3. WHEN a contact-host endpoint (`POST /contact-host`) is added to the Platform, THE responsible service SHALL apply a rate limit of 10 requests per 3600-second window per authenticated user using the shared `rate_limit` dependency.
4. WHERE the `contact-host` endpoint does not yet exist, THE Platform SHALL document this limit as a forward requirement to be applied at implementation time.

*Note: Requirement 7.1–7.2 is already implemented in `property_service/main.py`. These criteria formally document the existing behaviour.*

---

### Requirement 8: CORS Hardening

**User Story:** As a security engineer, I want every microservice to restrict CORS to the actual Rentora frontend domains, so that malicious third-party websites cannot make credentialled cross-origin requests to the API.

#### Acceptance Criteria

1. THE Platform SHALL configure every microservice's CORS middleware to use the Allowed_Origins list rather than the wildcard `"*"`.
2. WHILE the environment variable `ENV` is set to `production`, THE Service SHALL restrict `allow_origins` to `["https://rentora.in", "https://www.rentora.in", "https://app.rentora.in"]`.
3. WHILE the environment variable `ENV` is not set to `production`, THE Service SHALL restrict `allow_origins` to `["http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.1.5:5173"]`.
4. THE Service SHALL set `allow_credentials=True` only in combination with the explicit Allowed_Origins list, never alongside `allow_origins=["*"]`.
5. THE following Services Under Scope SHALL be updated to use the environment-driven Allowed_Origins pattern: `agreements_service`, `billing_service`, `maintenance_service`, `notification_service`, `onboarding_service`, `owner_dashboard_service`, `payment_service`, `profile_service`, `search_service`, `subscription_service`, `support_service`, `geo_amenity_service`.

---

### Requirement 9: HTTP Security Headers

**User Story:** As a security engineer, I want all microservices to emit standard HTTP security headers on every response, so that browsers apply click-jacking protection, MIME-sniffing prevention, and transport enforcement uniformly across the platform.

#### Acceptance Criteria

1. THE Service SHALL emit the `X-Frame-Options: DENY` header on every HTTP response.
2. THE Service SHALL emit the `X-Content-Type-Options: nosniff` header on every HTTP response.
3. THE Service SHALL emit the `X-XSS-Protection: 1; mode=block` header on every HTTP response.
4. THE Service SHALL emit the `Referrer-Policy: strict-origin-when-cross-origin` header on every HTTP response.
5. THE Service SHALL emit the `Permissions-Policy: geolocation=(), microphone=(), camera=()` header on every HTTP response.
6. WHILE the environment variable `ENV` is set to `production`, THE Service SHALL emit `Strict-Transport-Security: max-age=31536000; includeSubDomains` on every HTTPS response.
7. THE following Services Under Scope SHALL receive the Security_Headers_Middleware: `agreements_service`, `billing_service`, `maintenance_service`, `notification_service`, `onboarding_service`, `owner_dashboard_service`, `payment_service`, `profile_service`, `search_service`, `subscription_service`, `support_service`, `geo_amenity_service`.
8. THE Security_Headers_Middleware SHALL be implemented as a single reusable function in `shared_security.py` at the repository root, so that each service imports and mounts it rather than duplicating the implementation.

---

### Requirement 10: JWT Secret Externalisation

**User Story:** As a security engineer, I want every service to load the JWT signing secret from the `JWT_SECRET_KEY` environment variable, so that the secret is never committed to version control and can be rotated without a code change.

#### Acceptance Criteria

1. THE Service SHALL read the JWT signing secret exclusively via `os.environ.get("JWT_SECRET_KEY")` at module load time.
2. IF `JWT_SECRET_KEY` is not set in the environment, THEN THE Service SHALL fall back to the development default `"RENTORA_SUPER_SECRET_KEY"` and SHALL emit a `WARNING` level log message stating the secret is using the insecure default.
3. THE following services SHALL be updated to remove the hardcoded string literal and use the environment-variable pattern: `agreements_service`, `billing_service`, `maintenance_service`, `notification_service`, `owner_dashboard_service`, `payment_service`, `profile_service`, `subscription_service`, `support_service`.
4. THE `.env.example` file SHALL document the `JWT_SECRET_KEY` variable with a placeholder value and a comment explaining its purpose.

---

### Requirement 11: Frontend JWT Session Security

**User Story:** As a security engineer, I want the frontend to store the short-lived access token exclusively in React module memory and not in `localStorage`, so that an XSS vulnerability cannot exfiltrate a long-lived session credential.

#### Acceptance Criteria

1. THE Frontend SHALL store the `access_token` exclusively in the in-memory module-level variable `_accessToken` defined in `AuthContext.tsx` and SHALL NOT write it to `localStorage`, `sessionStorage`, or any cookie accessible to JavaScript.
2. WHEN a user logs in, THE Frontend SHALL call `localStorage.removeItem('token')` and `localStorage.removeItem('role')` to complete the migration of any previously stored tokens, as defined in the `login` callback of `AuthContext.tsx`.
3. WHEN a user logs out, THE Frontend SHALL clear `_accessToken` and `_role` from memory and SHALL call `localStorage.removeItem('token')` and `localStorage.removeItem('role')`.
4. THE Frontend SHALL provide a backward-compatibility bridge: WHEN the app mounts and `localStorage` contains a token from a previous session, THE Frontend SHALL read it into memory and then clear it from `localStorage`, allowing the existing session to remain active while completing the migration.
5. WHERE a Backend-For-Frontend (BFF) or same-origin reverse proxy is deployed in production, THE Platform SHOULD migrate the `access_token` to an `HttpOnly; Secure; SameSite=Strict` cookie, making it inaccessible to JavaScript entirely.
6. THE Auth_Service SHALL expose a `/auth/refresh` endpoint that accepts an `HttpOnly` refresh-token cookie and returns a new short-lived `access_token` in the JSON response body (not in a cookie), to support the future migration described in Requirement 11.5.

*Note: Requirements 11.1–11.4 describe behaviour already implemented in `AuthContext.tsx`. Requirement 11.5 and 11.6 are forward requirements for the production BFF phase.*

---

### Requirement 12: Shared Security Module

**User Story:** As a backend engineer, I want a single shared Python module that provides CORS configuration and security headers to all microservices, so that security-critical middleware is maintained in one place and consistently applied.

#### Acceptance Criteria

1. THE Platform SHALL provide a `shared_security.py` module at the repository root that exports two artefacts: `get_allowed_origins() -> list[str]` and `add_security_headers_middleware(app: FastAPI) -> None`.
2. WHEN `get_allowed_origins()` is called, THE Shared_Security_Module SHALL read the `ENV` environment variable and return the production origins list when `ENV == "production"` or the development origins list otherwise.
3. WHEN `add_security_headers_middleware(app)` is called, THE Shared_Security_Module SHALL register a single `@app.middleware("http")` function that appends all headers defined in Requirement 9.1–9.6.
4. THE Services Under Scope SHALL each call `add_security_headers_middleware(app)` and use `get_allowed_origins()` in their `CORSMiddleware` configuration, replacing any existing inline CORS or header middleware.
5. THE `shared_security.py` module SHALL be covered by at least one unit test that verifies the correct header values are present in a response and that the correct origins are returned for each environment value.
