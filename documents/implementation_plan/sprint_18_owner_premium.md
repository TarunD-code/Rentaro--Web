# Implementation Plan - Sprint 18: Owner Premium & Monetisation

Implement two new microservices and frontend modules to enable monetization and advanced analytics for property owners.

## Design Decisions
- **Database**: SQLite used for `rentora_billing.db` and `rentora_owner_dashboard.db`.
- **Storage**: Reports are saved in `uploads/reports`.
- **Payments**: Razorpay integration for Featured Listing purchases.

## Proposed Changes
### 1. New Services
- **billing_service**: Product catalog and checkout for featured placements.
- **owner_dashboard_service**: Metrics aggregation (revenue/occupancy) and PDF reporting.
### 2. Frontend Evolution
- **OwnerDashboard.tsx**: Analytics with Recharts.
- **FeaturedListings.tsx**: Monetization cards and checkout.
- **ReportCenter.tsx**: PDF management.

## Verification Plan
- Manual purchase flow verification.
- WeasyPrint PDF layout audit.
