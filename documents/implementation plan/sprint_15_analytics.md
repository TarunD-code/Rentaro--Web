# Sprint 15: Analytics Reporting & Admin Dashboard

## Goal
Establish a new centralized reporting engine to track platform-wide revenue, maintenance SLAs, payouts, and property occupancy. Provide Administrators with a bird's-eye view Dashboard and automated nightly/monthly report generations.

## Architecture & Integration

Given the Rentora platform currently operates on a decoupled SQLite microservices model (`rentora_profile.db`, `rentora_payments.db`, etc.), but the prompt specifies PostgreSQL, we have two viable architectural paths:
1. **Option A (Recommended for current local setup):** Implement `analytics_service` on port 8007 utilizing its own SQLite DB (`rentora_analytics.db`). Nightly Celery tasks (`refresh_reporting_views()`) will perform cross-DB ETL (Extract, Transform, Load) by fetching aggregates from endpoints or pulling from the local SQLite files securely, loading them into Analytics reporting tables.
2. **Option B (Strict PostgreSQL):** Standardize a PostgreSQL connection in `.env.example`. This requires running a local Postgres demon to run `seed_sprint15.sql` natively. 

We will proceed with **Option A** to maintain local continuity across the `.db` files, but all SQLAlchemy models and raw SQL seeding in `data/sql/seed_sprint15.sql` will be fully Postgres-compliant for future staging/prod environments.

## Proposed Changes

### New Service: `analytics_service` (Port 8007)
#### [NEW] `analytics_service/main.py`
Endpoints:
- `GET /admin/analytics/summary`: Revenue, payouts, occupancy rate.
- `GET /admin/analytics/ledger`: Grouped ledger aggregation.
- `GET /admin/analytics/maintenance`: SLA performance metrics.
- `GET /admin/analytics/payouts/reconciliation`: Failed constraints.
- `GET /admin/analytics/export`: Triggers WeasyPrint PDF/CSV.

#### [NEW] `analytics_service/models.py`
- `DailyAggregateSnapshot`: Tracks daily metrics mapped historically.
- `AuditLog`: Logs admin downloads and actions.

#### [NEW] `analytics_service/tasks.py`
Celery background workers:
- `refresh_reporting_views()`: Syncs data via ETL from other microservices into centralized reporting tables.
- `generate_monthly_admin_reports()`: Fires on the 1st of every month to generate the PDF via WeasyPrint and fake-mails to admins.

#### [MODIFY] `gateway/main.py`
Add prefix mapping for `/analytics -> http://127.0.0.1:8007`.

### Data Generators & Seeding
#### [NEW] `data/seeders/seed_sprint15.py`
We will build a mass-data seeder simulating historical data: 10 owners, 50 tenants, 80 properties, 120 agreements, 200 payment transactions, 30 maintenance requests.
#### [NEW] `data/sql/seed_sprint15.sql`
Raw SQL script providing minimal row setups as requested.
#### [NEW] `data/json/sample_reports.json`
Sample response structures for testing.

### Frontend Components (`epic7_sprint15_analytics_v1`)
#### [NEW] `frontend/src/pages/AdminAnalyticsDashboard.tsx`
Overview widgets: Revenue, Occupancy, Payouts, Maintenance SLA, Onboarding funnel, Move-out queue. Drilldown analytics and table views.
#### [MODIFY] `frontend/src/App.tsx`
Add routing.

### Testing
- `frontend/cypress/e2e/sprint15_analytics.cy.ts`: End-to-end dashboard rendering tests.
- `analytics_service/tests/test_analytics.py`: Test ETL tasks and role-based access.

## Verification Plan
1. Start `start.bat` including the new analytics service.
2. Run `make seed-sprint15` or `python data/seeders/seed_sprint15.py`.
3. Login as `admin`, verify dashboard widgets populate correctly.
4. Run `pytest` and `cypress`.
