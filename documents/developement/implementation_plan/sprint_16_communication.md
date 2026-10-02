# Implementation Plan - Sprint 16: Communication & Support (Epic E6)

Implement a real-time communication system including in-app chat (WebSockets), message history, and optional Twilio call masking.

## Goals
1. Implement real-time chat using WebSockets (Socket.IO).
2. Store and retrieve message history with pagination.
3. Integrate optional Twilio call masking for privacy.
4. Upgrade CI to Node.js 24.

## Proposed Changes

### [NEW] communication_service (Node.js/Express/TypeScript)
#### [NEW] `communication_service/package.json`
- Dependencies for Socket.IO, Express, SQLite3, and JWT.

#### [NEW] `communication_service/src/server.ts`
- Real-time event handling: `connect`, `disconnect`, `message`, `typing`.

#### [NEW] `communication_service/src/database.ts`
- SQLite integration for persisting `messages`.

### [MODIFY] gateway (FastAPI)
#### [MODIFY] `gateway/main.py`
- Route `/communication` requests to port `8007`.

### [MODIFY] frontend (React/TypeScript)
#### [NEW] `frontend/src/pages/ChatPage.tsx` & `ChatComponent.tsx`
- Socket.IO client integration, message list with auto-scroll, and typing indicators.

### [MODIFY] CI/CD
#### [MODIFY] `.github/workflows/ci.yml`
- Switch to Node.js 24 and configure the node-version environment.

## Verification
- Local build and lint checks.
- Cypress E2E tests for the real-time chat flow.
