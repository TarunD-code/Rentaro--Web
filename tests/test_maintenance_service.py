"""
Unit & Integration Tests for Maintenance Service — Sprint 12

Run: python -m pytest tests/test_maintenance_service.py -v
"""

import sys, os, datetime
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maintenance_service.database import SessionLocal, engine, Base
from maintenance_service import models


@pytest.fixture(scope="module")
def db():
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# ── Enum Tests ───────────────────────────────────────────────────────────────

class TestEnums:
    def test_request_categories(self):
        assert models.RequestCategory.plumbing.value == "plumbing"
        assert models.RequestCategory.electrical.value == "electrical"
        assert models.RequestCategory.cleaning.value == "cleaning"
        assert models.RequestCategory.pest_control.value == "pest_control"
        assert models.RequestCategory.carpentry.value == "carpentry"
        assert models.RequestCategory.other.value == "other"

    def test_request_priorities(self):
        assert models.RequestPriority.low.value == "low"
        assert models.RequestPriority.medium.value == "medium"
        assert models.RequestPriority.high.value == "high"
        assert models.RequestPriority.urgent.value == "urgent"

    def test_request_statuses(self):
        assert models.RequestStatus.open.value == "open"
        assert models.RequestStatus.assigned.value == "assigned"
        assert models.RequestStatus.in_progress.value == "in_progress"
        assert models.RequestStatus.resolved.value == "resolved"
        assert models.RequestStatus.closed.value == "closed"
        assert models.RequestStatus.cancelled.value == "cancelled"

    def test_assignment_statuses(self):
        assert models.AssignmentStatus.assigned.value == "assigned"
        assert models.AssignmentStatus.accepted.value == "accepted"
        assert models.AssignmentStatus.completed.value == "completed"


# ── Model CRUD Tests ────────────────────────────────────────────────────────

class TestMaintenanceRequestModel:

    def test_create_request(self, db):
        req = models.MaintenanceRequest(
            agreement_id=999, property_id=1,
            tenant_id="test_tenant_maint", owner_id="test_owner_maint",
            category="plumbing", title="Test tap leak",
            description="Test description", priority="high",
            status="open",
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        assert req.id is not None
        assert req.category == "plumbing"
        assert req.status == "open"
        assert req.priority == "high"

        db.delete(req)
        db.commit()

    def test_create_with_photos(self, db):
        req = models.MaintenanceRequest(
            property_id=1,
            tenant_id="photo_test_t", owner_id="photo_test_o",
            category="electrical", title="Photo test",
            photo_urls="url1.jpg,url2.jpg,url3.jpg",
            priority="medium", status="open",
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        photos = req.photo_urls.split(",")
        assert len(photos) == 3
        assert photos[0] == "url1.jpg"

        db.delete(req)
        db.commit()


class TestVendorAssignmentModel:

    def test_create_assignment(self, db):
        assignment = models.VendorAssignment(
            request_id=999,
            vendor_name="Test Plumber",
            vendor_phone="+91-1234567890",
            vendor_email="plumber@test.com",
            vendor_type="plumber",
            assigned_by="owner@test.com",
            cost_estimate=2000.0,
            status="assigned",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        assert assignment.id is not None
        assert assignment.vendor_name == "Test Plumber"
        assert assignment.cost_estimate == 2000.0

        db.delete(assignment)
        db.commit()

    def test_assignment_cost_tracking(self, db):
        assignment = models.VendorAssignment(
            request_id=998,
            vendor_name="Cost Tracker",
            assigned_by="owner@test.com",
            cost_estimate=3000.0,
            actual_cost=2800.0,
            status="completed",
            actual_date=datetime.datetime.utcnow(),
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        assert assignment.actual_cost == 2800.0
        assert assignment.cost_estimate - assignment.actual_cost == 200.0

        db.delete(assignment)
        db.commit()


# ── Status Transition Tests ──────────────────────────────────────────────────

class TestStatusTransitions:

    def test_full_request_lifecycle(self, db):
        """open → assigned → in_progress → resolved → closed"""
        req = models.MaintenanceRequest(
            property_id=1,
            tenant_id="lifecycle_t", owner_id="lifecycle_o",
            category="appliance", title="Lifecycle test",
            priority="medium", status="open",
        )
        db.add(req)
        db.commit()

        for status in ["assigned", "in_progress", "resolved", "closed"]:
            req.status = status
            if status == "resolved":
                req.resolved_at = datetime.datetime.utcnow()
                req.resolution_notes = "Fixed by vendor"
            if status == "closed":
                req.closed_at = datetime.datetime.utcnow()
            db.commit()
            assert req.status == status

        assert req.resolved_at is not None
        assert req.closed_at is not None
        assert req.resolution_notes == "Fixed by vendor"

        db.delete(req)
        db.commit()

    def test_cancellation(self, db):
        req = models.MaintenanceRequest(
            property_id=1,
            tenant_id="cancel_t", owner_id="cancel_o",
            category="other", title="Cancel test",
            priority="low", status="open",
        )
        db.add(req)
        db.commit()

        req.status = "cancelled"
        db.commit()
        assert req.status == "cancelled"

        db.delete(req)
        db.commit()

    def test_assignment_lifecycle(self, db):
        """assigned → accepted → in_progress → completed"""
        a = models.VendorAssignment(
            request_id=997,
            vendor_name="Lifecycle Vendor",
            assigned_by="owner@test.com",
            status="assigned",
        )
        db.add(a)
        db.commit()

        for status in ["accepted", "in_progress", "completed"]:
            a.status = status
            if status == "completed":
                a.actual_date = datetime.datetime.utcnow()
                a.actual_cost = 1500.0
            db.commit()
            assert a.status == status

        assert a.actual_date is not None
        assert a.actual_cost == 1500.0

        db.delete(a)
        db.commit()


# ── Integration Flow Tests ───────────────────────────────────────────────────

class TestMaintenanceFlow:

    def test_tenant_to_resolution_flow(self, db):
        """Full flow: tenant creates → owner assigns vendor → vendor resolves."""
        # 1. Tenant creates request
        req = models.MaintenanceRequest(
            agreement_id=996, property_id=1,
            tenant_id="flow_t", owner_id="flow_o",
            category="plumbing", title="Bathroom tap dripping",
            description="Hot water tap dripping in master bathroom",
            priority="high", status="open",
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        assert req.status == "open"

        # 2. Owner assigns vendor
        vendor = models.VendorAssignment(
            request_id=req.id,
            vendor_name="Rajesh Plumbing",
            vendor_phone="+91-9999999999",
            vendor_type="plumber",
            assigned_by="flow_o",
            cost_estimate=1200.0,
            status="assigned",
        )
        db.add(vendor)
        req.status = "assigned"
        db.commit()
        assert req.status == "assigned"

        # 3. Vendor starts work
        vendor.status = "in_progress"
        req.status = "in_progress"
        db.commit()

        # 4. Vendor completes
        vendor.status = "completed"
        vendor.actual_cost = 1000.0
        vendor.actual_date = datetime.datetime.utcnow()
        req.status = "resolved"
        req.resolved_at = datetime.datetime.utcnow()
        req.resolution_notes = "Replaced tap washer and tightened fitting."
        db.commit()

        assert req.status == "resolved"
        assert vendor.status == "completed"
        assert vendor.actual_cost < vendor.cost_estimate  # Under budget

        # Cleanup
        db.delete(vendor)
        db.delete(req)
        db.commit()

    def test_multiple_vendors_for_one_request(self, db):
        """A request can have multiple vendor assignments."""
        req = models.MaintenanceRequest(
            property_id=1,
            tenant_id="multi_t", owner_id="multi_o",
            category="electrical", title="Multi vendor test",
            priority="medium", status="open",
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        # First vendor cancelled
        v1 = models.VendorAssignment(
            request_id=req.id, vendor_name="Vendor A",
            assigned_by="multi_o", status="cancelled",
        )
        # Second vendor completes
        v2 = models.VendorAssignment(
            request_id=req.id, vendor_name="Vendor B",
            assigned_by="multi_o", status="completed",
            actual_cost=2000.0, actual_date=datetime.datetime.utcnow(),
        )
        db.add_all([v1, v2])
        db.commit()

        assignments = db.query(models.VendorAssignment).filter(
            models.VendorAssignment.request_id == req.id,
        ).all()
        assert len(assignments) == 2

        db.delete(v1)
        db.delete(v2)
        db.delete(req)
        db.commit()

    def test_priority_query(self, db):
        """Can filter by priority."""
        for p in ["low", "medium", "high", "urgent"]:
            r = models.MaintenanceRequest(
                property_id=1,
                tenant_id=f"prio_{p}_t", owner_id=f"prio_{p}_o",
                category="other", title=f"Priority {p} test",
                priority=p, status="open",
            )
            db.add(r)
        db.commit()

        urgent = db.query(models.MaintenanceRequest).filter(
            models.MaintenanceRequest.priority == "urgent",
            models.MaintenanceRequest.tenant_id.like("prio_%"),
        ).all()
        assert len(urgent) == 1

        # Cleanup
        db.query(models.MaintenanceRequest).filter(
            models.MaintenanceRequest.tenant_id.like("prio_%"),
        ).delete(synchronize_session="fetch")
        db.commit()
