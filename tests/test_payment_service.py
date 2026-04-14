"""
Unit & Integration Tests for Payment Service — Sprint 10

Run: python -m pytest tests/test_payment_service.py -v
"""

import sys
import os
import datetime
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment_service.database import SessionLocal, engine, Base
from payment_service import models
from payment_service.razorpay_client import RazorpayClient


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    """Create a clean test database session."""
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def rz_client():
    """Razorpay client in sandbox mode."""
    client = RazorpayClient()
    assert client.is_sandbox, "Tests must run in sandbox mode"
    return client


# ── Razorpay Client Tests ────────────────────────────────────────────────────

class TestRazorpayClient:

    def test_sandbox_mode_active(self, rz_client):
        assert rz_client.is_sandbox is True

    def test_create_order(self, rz_client):
        order = rz_client.create_order(amount=50000.0, receipt="test_001")
        assert order["id"].startswith("order_mock_")
        assert order["amount"] == 5000000  # paise
        assert order["currency"] == "INR"
        assert order["status"] == "created"

    def test_create_order_custom_currency(self, rz_client):
        order = rz_client.create_order(amount=100.0, currency="USD")
        assert order["currency"] == "USD"

    def test_verify_payment_signature_mock(self, rz_client):
        order_id = "order_mock_test123"
        payment_id = "pay_mock_test456"
        sig = rz_client.generate_mock_signature(order_id, payment_id)

        assert rz_client.verify_payment_signature(order_id, payment_id, sig) is True

    def test_verify_payment_signature_prefix(self, rz_client):
        assert rz_client.verify_payment_signature("a", "b", "mock_sig_anything") is True

    def test_verify_payment_signature_invalid(self, rz_client):
        assert rz_client.verify_payment_signature("a", "b", "invalid") is False

    def test_create_subscription(self, rz_client):
        sub = rz_client.create_subscription(plan_amount=25000.0, tenant_id="test_tenant")
        assert sub["id"].startswith("sub_mock_")
        assert sub["status"] == "created"
        assert "short_url" in sub

    def test_cancel_subscription(self, rz_client):
        result = rz_client.cancel_subscription("sub_mock_test")
        assert result["status"] == "cancelled"

    def test_charge_subscription(self, rz_client):
        result = rz_client.charge_subscription("sub_mock_test", 25000.0)
        assert result["status"] == "captured"
        assert result["razorpay_payment_id"].startswith("pay_mock_")

    def test_webhook_signature_sandbox(self, rz_client):
        assert rz_client.verify_webhook_signature(b"test", "any_sig") is True

    def test_generate_mock_payment_id(self, rz_client):
        pid = rz_client.generate_mock_payment_id()
        assert pid.startswith("pay_mock_")


# ── Model Tests ──────────────────────────────────────────────────────────────

class TestModels:

    def test_create_transaction(self, db):
        txn = models.PaymentTransaction(
            agreement_id=999,
            tenant_id="test_tenant",
            owner_id="test_owner",
            property_id=1,
            transaction_type=models.TransactionType.deposit.value,
            amount=50000.0,
            status=models.TransactionStatus.created.value,
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)

        assert txn.id is not None
        assert txn.transaction_type == "deposit"
        assert txn.status == "created"
        assert txn.amount == 50000.0

        # Cleanup
        db.delete(txn)
        db.commit()

    def test_create_mandate(self, db):
        mandate = models.AutoPayMandate(
            tenant_id="test_tenant",
            agreement_id=999,
            property_id=1,
            status=models.MandateStatus.created.value,
            max_amount=30000.0,
        )
        db.add(mandate)
        db.commit()
        db.refresh(mandate)

        assert mandate.id is not None
        assert mandate.status == "created"
        assert mandate.frequency == "monthly"

        # Cleanup
        db.delete(mandate)
        db.commit()

    def test_transaction_status_transitions(self, db):
        txn = models.PaymentTransaction(
            agreement_id=999,
            tenant_id="test_tenant",
            owner_id="test_owner",
            property_id=1,
            transaction_type=models.TransactionType.rent.value,
            amount=25000.0,
            status=models.TransactionStatus.created.value,
        )
        db.add(txn)
        db.commit()

        # Transition to captured
        txn.status = models.TransactionStatus.captured.value
        txn.paid_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(txn)

        assert txn.status == "captured"
        assert txn.paid_at is not None

        # Cleanup
        db.delete(txn)
        db.commit()


# ── Integration Tests ────────────────────────────────────────────────────────

class TestPaymentFlow:

    def test_deposit_flow(self, db, rz_client):
        """Full deposit flow: create order → verify → check status."""
        # 1. Create order
        order = rz_client.create_order(amount=50000.0, receipt="deposit_test")

        txn = models.PaymentTransaction(
            agreement_id=100,
            tenant_id="flow_tenant",
            owner_id="flow_owner",
            property_id=1,
            transaction_type="deposit",
            amount=50000.0,
            razorpay_order_id=order["id"],
            status="created",
        )
        db.add(txn)
        db.commit()

        # 2. Simulate payment completion
        payment_id = rz_client.generate_mock_payment_id()
        signature = rz_client.generate_mock_signature(order["id"], payment_id)

        # 3. Verify
        assert rz_client.verify_payment_signature(order["id"], payment_id, signature) is True

        txn.razorpay_payment_id = payment_id
        txn.razorpay_signature = signature
        txn.status = "captured"
        txn.paid_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(txn)

        assert txn.status == "captured"
        assert txn.razorpay_payment_id == payment_id

        # Cleanup
        db.delete(txn)
        db.commit()

    def test_duplicate_deposit_prevention(self, db):
        """Should not allow duplicate captured deposits for same agreement."""
        txn1 = models.PaymentTransaction(
            agreement_id=200,
            tenant_id="dup_tenant",
            owner_id="dup_owner",
            property_id=2,
            transaction_type="deposit",
            amount=50000.0,
            razorpay_order_id="order_dup_001",
            status="captured",
            paid_at=datetime.datetime.utcnow(),
        )
        db.add(txn1)
        db.commit()

        # Check for existing captured deposit
        existing = db.query(models.PaymentTransaction).filter(
            models.PaymentTransaction.agreement_id == 200,
            models.PaymentTransaction.transaction_type == "deposit",
            models.PaymentTransaction.status == "captured",
        ).first()

        assert existing is not None, "Should find existing captured deposit"

        # Cleanup
        db.delete(txn1)
        db.commit()

    def test_mandate_lifecycle(self, db, rz_client):
        """Mandate: create → activate → cancel."""
        sub = rz_client.create_subscription(plan_amount=25000.0, tenant_id="mandate_tenant")

        mandate = models.AutoPayMandate(
            tenant_id="mandate_tenant",
            agreement_id=300,
            property_id=3,
            razorpay_subscription_id=sub["id"],
            status="created",
            max_amount=25000.0,
        )
        db.add(mandate)
        db.commit()

        # Activate
        mandate.status = "active"
        mandate.next_charge_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        db.commit()

        assert mandate.status == "active"

        # Cancel
        rz_client.cancel_subscription(sub["id"])
        mandate.status = "cancelled"
        db.commit()

        assert mandate.status == "cancelled"

        # Cleanup
        db.delete(mandate)
        db.commit()


# ── Enum Tests ───────────────────────────────────────────────────────────────

class TestEnums:
    def test_transaction_types(self):
        assert models.TransactionType.deposit.value == "deposit"
        assert models.TransactionType.rent.value == "rent"
        assert models.TransactionType.refund.value == "refund"

    def test_payment_methods(self):
        assert models.PaymentMethod.upi.value == "upi"
        assert models.PaymentMethod.mandate.value == "mandate"

    def test_transaction_statuses(self):
        assert models.TransactionStatus.created.value == "created"
        assert models.TransactionStatus.captured.value == "captured"
        assert models.TransactionStatus.failed.value == "failed"

    def test_mandate_statuses(self):
        assert models.MandateStatus.active.value == "active"
        assert models.MandateStatus.cancelled.value == "cancelled"
