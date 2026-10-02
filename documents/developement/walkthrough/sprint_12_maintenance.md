# Sprint 12: Walkthrough — Maintenance & Service Requests

**Flag**: `epic7_sprint12_maintenance_v1` | **Port**: 8005

## What Was Built
New `maintenance_service` microservice for tenant service requests, owner/vendor assignment, status tracking, and maintenance history.

## Key Files Created
| File | Purpose |
|------|---------|
| `maintenance_service/__init__.py` | Package init |
| `maintenance_service/database.py` | SQLite config |
| `maintenance_service/models.py` | MaintenanceRequest, VendorAssignment |
| `maintenance_service/schemas.py` | Pydantic V2 schemas |
| `maintenance_service/main.py` | 11 API endpoints |
| `maintenance_service/tasks.py` | Celery-ready tasks |
| `maintenance_service/templates/new_request.html` | New request email |
| `maintenance_service/templates/vendor_assigned.html` | Assignment email |
| `maintenance_service/templates/request_resolved.html` | Resolution email |
| `frontend/src/pages/ServiceRequestForm.tsx` | Category/priority form |
| `frontend/src/pages/OwnerAssignmentPanel.tsx` | Vendor assignment panel |
| `frontend/src/pages/VendorTaskView.tsx` | Task stepper + resolution |
| `frontend/src/pages/MaintenanceHistory.tsx` | History table + CSV export |
| `frontend/src/components/MaintenanceStatusCard.tsx` | Dashboard widget |
| `scripts/seed_maintenance.py` | Seed (4 requests + 2 assignments) |
| `tests/test_maintenance_service.py` | 14 tests |
| `frontend/cypress/e2e/sprint12_maintenance.cy.ts` | E2E tests |

## Models
- **MaintenanceRequest**: 8 categories, 4 priorities, 6 statuses, resolution tracking
- **VendorAssignment**: Vendor contact details, cost estimate vs actual, status lifecycle
- Enums: RequestCategory, RequestPriority, RequestStatus, AssignmentStatus

## Modified Files
- `gateway/main.py` — Added MAINTENANCE_SERVICE_URL + route
- `start.bat` — Added maintenance service startup
- `App.tsx` — Added 4 routes
- `TenantDashboard.tsx` — Added MaintenanceStatusCard
- `OwnerDashboard.tsx` — Added MaintenanceStatusCard
- `featureFlags.ts` — Added epic7_sprint12_maintenance_v1

## API Endpoints (11 total)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/maintenance/request` | Create request |
| GET | `/maintenance/request/{id}` | Get details |
| GET | `/maintenance/requests` | List (role-filtered) |
| GET | `/maintenance/requests/active` | Active requests |
| PUT | `/maintenance/request/{id}/status` | Update status |
| POST | `/maintenance/assign` | Assign vendor |
| GET | `/maintenance/assignments/{id}` | Get assignments |
| PUT | `/maintenance/assignment/{id}/status` | Vendor updates |
| GET | `/maintenance/history` | Filtered history |
| GET | `/maintenance/history/export` | CSV export |
| GET | `/maintenance/stats` | Dashboard stats |

## Status Transitions
```
Request:    open → assigned → in_progress → resolved → closed
Assignment: assigned → accepted → in_progress → completed
```

## Testing — 14/14 Passed
- Enums (4) | Models (2) | Assignments (2) | Transitions (3) | Flow (3)

## API Smoke Results
- `GET /requests/active` → 4 requests ✅
- `GET /stats` → total=4, open=2, in_progress=1, resolved=1 ✅
- `POST /request` → Created "AC not cooling" (appliance, high) ✅

## Seed Data
- 4 requests: plumbing (open), electrical (in_progress), cleaning (resolved), pest_control (assigned)
- 2 vendor assignments: Suresh Electricals (in_progress), PestFree Solutions (assigned)
