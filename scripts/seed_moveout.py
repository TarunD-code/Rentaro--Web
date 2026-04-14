"""
Seed Move-Out Demo Data — Sprint 11

Creates sample move-out requests and settlements for testing.
Run: python -m scripts.seed_moveout
"""

import sys, os, datetime, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment_service.database import SessionLocal, engine
from payment_service import models


def seed():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.datetime.utcnow()

    # Check if already seeded
    existing = db.query(models.MoveOutRequest).first()
    if existing:
        print("Move-out data already seeded. Skipping.")
        db.close()
        return

    print("Seeding move-out data...")

    # 1. Active move-out in notice period (15 days remaining)
    mo1 = models.MoveOutRequest(
        agreement_id=1,
        property_id=1,
        tenant_id="admin@rentora.com",
        owner_id="owner@rentora.com",
        status=models.MoveOutStatus.notice_period.value,
        notice_period_days=30,
        reason="Relocating for work",
        initiated_at=now - datetime.timedelta(days=15),
        expected_vacate_date=now + datetime.timedelta(days=15),
        created_at=now - datetime.timedelta(days=15),
    )
    db.add(mo1)
    db.flush()
    print(f"  Added move-out #{mo1.id} (notice_period, 15 days left)")

    # 2. Completed move-out with finalized settlement
    mo2 = models.MoveOutRequest(
        agreement_id=2,
        property_id=2,
        tenant_id="tenant2@rentora.com",
        owner_id="owner@rentora.com",
        status=models.MoveOutStatus.completed.value,
        notice_period_days=30,
        reason="Lease not renewed",
        initiated_at=now - datetime.timedelta(days=60),
        expected_vacate_date=now - datetime.timedelta(days=30),
        actual_vacate_date=now - datetime.timedelta(days=28),
        created_at=now - datetime.timedelta(days=60),
    )
    db.add(mo2)
    db.flush()
    print(f"  Added move-out #{mo2.id} (completed)")

    # Settlement for completed move-out
    deductions = [
        {"category": "cleaning", "description": "Deep cleaning of kitchen and bathrooms", "amount": 3000},
        {"category": "damages", "description": "Wall paint scratches in bedroom", "amount": 5000},
    ]

    stl = models.SettlementRecord(
        moveout_id=mo2.id,
        agreement_id=2,
        tenant_id="tenant2@rentora.com",
        owner_id="owner@rentora.com",
        deposit_amount=50000.0,
        pending_rent=0.0,
        cleaning_charge=3000.0,
        damage_charge=5000.0,
        total_deductions=8000.0,
        refund_amount=42000.0,
        deductions_json=json.dumps(deductions),
        owner_notes="Minor wear and tear. Kitchen needed deep cleaning.",
        settlement_pdf_url="/payment/moveout/settlement/1/html",
        status=models.SettlementStatus.finalized.value,
        finalized_at=now - datetime.timedelta(days=25),
        created_at=now - datetime.timedelta(days=28),
    )
    db.add(stl)
    print(f"  Added settlement (deposit: 50000, deductions: 8000, refund: 42000)")

    db.commit()
    db.close()
    print("[OK] Move-out seed complete!")


if __name__ == "__main__":
    seed()
