# Sprint 15 Walkthrough: Analytics Reporting & Admin Dashboard

## Overview
Successfully implemented the `analytics_service` to aggregate and monitor Rentora's global revenue, payouts, properties occupancy, and maintenance SLAs. This infrastructure safely consolidates historical snapshots into a centralized reporting Database.

## Architectural Additions

### Microservice: `analytics_service` 
- Created an independent FastAPI service on Port `8007` operating `rentora_analytics.db`.
- **Data Models**: Added `DailyAggregateSnapshot` for materialized views of KPI tracking, and `AuditLog` to heavily restrict and track admin payload extractions.

### Backend APIs
Created role-guarded Endpoints:
- `GET /admin/analytics/summary`: Real-time pull of Occupancy Rates, Revenue aggregations, and Refund figures.
- `GET /admin/analytics/ledger`: Financial period-over-period tracking.
- `GET /admin/analytics/maintenance`: SLA performance metrics (Open vs Overdue calculations).
- `GET /admin/analytics/payouts/reconciliation`: Identification of mismatches between the payment edge and Razorpay settlement clusters.
- `GET /admin/analytics/export`: Triggers secure document conversion.

### Celery Pipelines
- `refresh_reporting_views()`: Background ETL worker simulated to run nightly, converting live unstructured cross-DB schemas into clean, highly-indexable `DailyAggregateSnapshot` structures.
- `generate_monthly_admin_reports()`: End-of-month WeasyPrint execution bot.

## Feature Testing Seeders
Introduced mass-scale Mock Data Seeders into the data repository (`data/seeders/seed_sprint15.py` and `data/sql/seed_sprint15.sql`) capable of filling the datastore with heavily varied combinations of simulated owners, tenants, and properties suitable for deep Analytics integration testing.
A CLI Make command was attached: `make seed-sprint15`.

## Frontend Admin UI
- Constructed `AdminAnalyticsDashboard.tsx` utilizing modern material charts and unified KPI grids mapping directly to the new reporting pipelines.
- Masked securely via the `epic7_sprint15_analytics_v1` dark-launch feature flag in `featureFlags.ts`.

## QA Validation
- Validated via standard integration routing in `analytics_service/tests/test_analytics.py`.
- Simulated frontend flow via End-to-End browser interactions encoded in `frontend/cypress/e2e/sprint15_analytics.cy.ts`.
- CI automations enabled targeting the `seed-sprint15` target in `.github/workflows/ci.yml`.
