# Walkthrough - Sprint 17: Unified Notification System

Modernized Rentora's communication layer with a scalable, event-driven architecture.

## Key Accomplishments
- **Hub Architecture**: Created a single service that decouples notification logic from individual microservices.
- **Templating Engine**: Dynamically generated HTML emails and SMS messages based on metadata.
- **FCM Real-time**: Implemented web-push notifications to ensure tenants never miss a critical update.

## Verification
- Verified Kafka consumers are correctly picking up property-link events.
- Successfully delivered test the "Rent Due" reminder to mobile and email.
