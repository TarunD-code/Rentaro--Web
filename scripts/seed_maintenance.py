"""
Seed Maintenance Demo Data — Sprint 12

Creates sample maintenance requests and vendor assignments.
Run: python -m scripts.seed_maintenance
"""

import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maintenance_service.database import SessionLocal, engine
from maintenance_service import models


def seed():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.datetime.utcnow()

    existing = db.query(models.MaintenanceRequest).first()
    if existing:
        print("Maintenance data already seeded. Skipping.")
        db.close()
        return

    print("Seeding maintenance data...")

    # 1. Open request (high priority)
    r1 = models.MaintenanceRequest(
        agreement_id=1, property_id=1,
        tenant_id="admin@rentora.com", owner_id="owner@rentora.com",
        category="plumbing", title="Kitchen tap leaking badly",
        description="The kitchen sink tap has been dripping continuously for 2 days. Water pooling under the sink.",
        priority="high", status="open",
        created_at=now - datetime.timedelta(hours=6),
    )
    db.add(r1)
    db.flush()
    print(f"  Added request #{r1.id} (plumbing, open, high)")

    # 2. In-progress request with vendor assigned
    r2 = models.MaintenanceRequest(
        agreement_id=1, property_id=1,
        tenant_id="admin@rentora.com", owner_id="owner@rentora.com",
        category="electrical", title="Living room light fixture flickering",
        description="The main ceiling light in the living room flickers intermittently.",
        priority="medium", status="in_progress",
        created_at=now - datetime.timedelta(days=3),
    )
    db.add(r2)
    db.flush()
    print(f"  Added request #{r2.id} (electrical, in_progress, medium)")

    # Vendor assignment for r2
    a1 = models.VendorAssignment(
        request_id=r2.id,
        vendor_name="Suresh Electricals",
        vendor_phone="+91-9876543210",
        vendor_email="suresh@electricals.com",
        vendor_type="electrician",
        assigned_by="owner@rentora.com",
        estimated_date=now + datetime.timedelta(days=1),
        cost_estimate=1500.0,
        status="in_progress",
        created_at=now - datetime.timedelta(days=2),
    )
    db.add(a1)
    print(f"  Added vendor assignment: Suresh Electricals -> request #{r2.id}")

    # 3. Resolved request
    r3 = models.MaintenanceRequest(
        agreement_id=1, property_id=1,
        tenant_id="admin@rentora.com", owner_id="owner@rentora.com",
        category="cleaning", title="Deep cleaning of bathrooms",
        description="Both bathrooms need thorough cleaning including tile scrubbing.",
        priority="low", status="resolved",
        resolution_notes="Deep cleaned both bathrooms. Replaced damaged shower curtain.",
        resolved_at=now - datetime.timedelta(days=5),
        created_at=now - datetime.timedelta(days=10),
    )
    db.add(r3)
    db.flush()
    print(f"  Added request #{r3.id} (cleaning, resolved, low)")

    # 4. Pest control request (urgent)
    r4 = models.MaintenanceRequest(
        agreement_id=1, property_id=1,
        tenant_id="admin@rentora.com", owner_id="owner@rentora.com",
        category="pest_control", title="Cockroach infestation in kitchen",
        description="Multiple cockroaches spotted in kitchen cabinets and near the fridge.",
        priority="urgent", status="assigned",
        created_at=now - datetime.timedelta(hours=12),
    )
    db.add(r4)
    db.flush()

    a2 = models.VendorAssignment(
        request_id=r4.id,
        vendor_name="PestFree Solutions",
        vendor_phone="+91-9123456789",
        vendor_email="service@pestfree.in",
        vendor_type="pest_control",
        assigned_by="owner@rentora.com",
        estimated_date=now + datetime.timedelta(hours=6),
        cost_estimate=2500.0,
        status="assigned",
        created_at=now - datetime.timedelta(hours=6),
    )
    db.add(a2)
    print(f"  Added request #{r4.id} (pest_control, assigned, urgent)")

    db.commit()
    db.close()
    print("[OK] Maintenance seed complete!")


if __name__ == "__main__":
    seed()
