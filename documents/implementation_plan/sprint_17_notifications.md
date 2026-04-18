# Implementation Plan - Sprint 17: Unified Notification System

Build an event-driven notification engine that centralizes all platform communications (FCM, SMS, Email).

## Proposed Changes
### 1. Infrastructure: Kafka Integration
- Use Kafka topics for domain events (e.g., `payment.received`, `agreement.signed`).
### 2. Backend: Communication Service
- **Logic**: Multi-channel dispatching engine.
- **Providers**: Twilio (SMS), Firebase (Push), SMTP (Email).
### 3. Frontend: Notification Center
- Persistent drawer for user notifications and real-time toast alerts.

## Verification Plan
- Trigger a mock Kafka event and verify delivery across all three channels.
- Test notification "Mark as Read" functionality.
