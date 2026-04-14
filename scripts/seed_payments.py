"""
Seed script for payment service — creates demo transactions and mandates.
Run: python -m scripts.seed_payments
"""

import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment_service.database import SessionLocal, engine
from payment_service import models

# Create tables
models.Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()

    # Check if already seeded
    existing = db.query(models.PaymentTransaction).count()
    if existing > 0:
        print(f"Already have {existing} transactions — skipping seed")
        db.close()
        return

    print("Seeding payment transactions...")

    now = datetime.datetime.utcnow()
    last_month = now - datetime.timedelta(days=30)
    two_months_ago = now - datetime.timedelta(days=60)
    next_month = now + datetime.timedelta(days=30)

    transactions = [
        # Deposit — paid
        models.PaymentTransaction(
            agreement_id=1,
            tenant_id="admin@rentora.com",
            owner_id="owner@rentora.com",
            property_id=1,
            transaction_type="deposit",
            payment_method="upi",
            amount=50000.0,
            razorpay_order_id="order_mock_deposit_001",
            razorpay_payment_id="pay_mock_deposit_001",
            status="captured",
            paid_at=two_months_ago,
            receipt_url="/payment/receipt/1",
            created_at=two_months_ago,
        ),
        # Rent — paid (2 months ago)
        models.PaymentTransaction(
            agreement_id=1,
            tenant_id="admin@rentora.com",
            owner_id="owner@rentora.com",
            property_id=1,
            transaction_type="rent",
            payment_method="card",
            amount=25000.0,
            razorpay_order_id="order_mock_rent_001",
            razorpay_payment_id="pay_mock_rent_001",
            status="captured",
            due_date=two_months_ago.replace(day=1),
            paid_at=two_months_ago,
            receipt_url="/payment/receipt/2",
            created_at=two_months_ago,
        ),
        # Rent — paid (last month)
        models.PaymentTransaction(
            agreement_id=1,
            tenant_id="admin@rentora.com",
            owner_id="owner@rentora.com",
            property_id=1,
            transaction_type="rent",
            payment_method="mandate",
            amount=25000.0,
            razorpay_order_id="order_mock_rent_002",
            razorpay_payment_id="pay_mock_rent_002",
            status="captured",
            due_date=last_month.replace(day=1),
            paid_at=last_month,
            receipt_url="/payment/receipt/3",
            created_at=last_month,
        ),
        # Rent — upcoming (next month)
        models.PaymentTransaction(
            agreement_id=1,
            tenant_id="admin@rentora.com",
            owner_id="owner@rentora.com",
            property_id=1,
            transaction_type="rent",
            payment_method=None,
            amount=25000.0,
            razorpay_order_id="order_mock_rent_003",
            status="created",
            due_date=next_month.replace(day=1),
            created_at=now,
        ),
        # Rent — failed (for retry testing)
        models.PaymentTransaction(
            agreement_id=1,
            tenant_id="admin@rentora.com",
            owner_id="owner@rentora.com",
            property_id=1,
            transaction_type="rent",
            payment_method="card",
            amount=25000.0,
            razorpay_order_id="order_mock_rent_fail",
            status="failed",
            failure_reason="Card declined — insufficient funds",
            due_date=now.replace(day=1),
            retry_count=1,
            created_at=now - datetime.timedelta(days=2),
        ),
    ]

    for txn in transactions:
        db.add(txn)

    print(f"Added {len(transactions)} transactions")

    # Seed auto-pay mandate
    mandate = models.AutoPayMandate(
        tenant_id="admin@rentora.com",
        agreement_id=1,
        property_id=1,
        razorpay_subscription_id="sub_mock_autopay_001",
        status="active",
        max_amount=30000.0,
        frequency="monthly",
        start_date=two_months_ago,
        next_charge_date=next_month.replace(day=1),
        created_at=two_months_ago,
    )
    db.add(mandate)
    print("Added 1 auto-pay mandate (active)")

    db.commit()
    db.close()
    print("[OK] Payment seed complete!")


if __name__ == "__main__":
    seed()
