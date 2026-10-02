# Sprint 12: Implementation Plan — Maintenance & Service Requests

**Date**: April 14, 2026 | **Flag**: `epic7_sprint12_maintenance_v1`

## Goal
Implement tenant service request workflows, owner/vendor assignment, status tracking, and maintenance history with CSV export.

## Architecture Decision
- New `maintenance_service` microservice on port 8005, isolated `rentora_maintenance.db`
- Separate from payment_service as it's a distinct domain (work orders, not financial)
- 8 request categories, 4 priority levels, 6 status states
- Vendor assignment with cost tracking (estimate vs actual)

## Proposed Changes

### 1. New Microservice — `maintenance_service/` (Port 8005)
- `database.py` — SQLAlchemy engine → `rentora_maintenance.db`
- `models.py`:
  - **MaintenanceRequest**: category (plumbing/electrical/cleaning/appliance/pest_control/carpentry/painting/other), title, description, photo_urls, priority (low/medium/high/urgent), status (open→assigned→in_progress→resolved→closed→cancelled)
  - **VendorAssignment**: vendor details, cost tracking, status lifecycle
- `schemas.py` — Pydantic V2 schemas
- `main.py` — 11 API endpoints
- `tasks.py` — Async task stubs

### 2. API Design (11 endpoints)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/request` | Create request |
| GET | `/request/{id}` | Get details |
| GET | `/requests` | List (role-filtered) |
| GET | `/requests/active` | Active requests |
| PUT | `/request/{id}/status` | Update status |
| POST | `/assign` | Assign vendor |
| GET | `/assignments/{req_id}` | Get assignments |
| PUT | `/assignment/{id}/status` | Vendor updates |
| GET | `/history` | Filtered history |
| GET | `/history/export` | CSV export |
| GET | `/stats` | Dashboard stats |

### 3. Frontend (4 pages + 1 widget)
- ServiceRequestForm: Category chips, priority, description
- OwnerAssignmentPanel: Request cards + vendor dialog
- VendorTaskView: Task stepper + resolution dialog
- MaintenanceHistory: Filterable table + CSV export
- MaintenanceStatusCard: Dashboard stats

### 4. Infrastructure
- Gateway: `maintenance/*` → port 8005
- `start.bat` updated
- Email templates: new_request, vendor_assigned, request_resolved

## Verification
- 14 backend tests
- API smoke tests for all endpoints
- Cypress E2E tests
