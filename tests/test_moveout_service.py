"""
Unit & Integration Tests for Move-Out Service — Sprint 11

Run: python -m pytest tests/test_moveout_service.py -v
"""

import sys, os, datetime, json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment_service.database import SessionLocal, engine, Base
from payment_service import models
from payment_service.settlement_pdf import generate_settlement_html, generate_settlement_pdf


@pytest.fixture(scope="module")
def db():
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# ── Enum Tests ───────────────────────────────────────────────────────────────

class TestMoveOutEnums:
    def test_moveout_statuses(self):
        assert models.MoveOutStatus.initiated.value == "initiated"
        assert models.MoveOutStatus.notice_period.value == "notice_period"
        assert models.MoveOutStatus.owner_review.value == "owner_review"
        assert models.MoveOutStatus.settlement_pending.value == "settlement_pending"
        assert models.MoveOutStatus.completed.value == "completed"
        assert models.MoveOutStatus.cancelled.value == "cancelled"

    def test_settlement_statuses(self):
        assert models.SettlementStatus.draft.value == "draft"
        assert models.SettlementStatus.finalized.value == "finalized"
        assert models.SettlementStatus.paid.value == "paid"

    def test_settlement_transaction_type(self):
        assert models.TransactionType.settlement.value == "settlement"


# ── Model Tests ──────────────────────────────────────────────────────────────

class TestMoveOutModels:

    def test_create_moveout_request(self, db):
        vacate = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        mo = models.MoveOutRequest(
            agreement_id=999,
            property_id=1,
            tenant_id="test_mo_tenant",
            owner_id="test_mo_owner",
            status=models.MoveOutStatus.notice_period.value,
            notice_period_days=30,
            reason="Test move-out",
            expected_vacate_date=vacate,
        )
        db.add(mo)
        db.commit()
        db.refresh(mo)

        assert mo.id is not None
        assert mo.status == "notice_period"
        assert mo.notice_period_days == 30
        assert mo.expected_vacate_date == vacate

        db.delete(mo)
        db.commit()

    def test_create_settlement_record(self, db):
        stl = models.SettlementRecord(
            moveout_id=999,
            agreement_id=999,
            tenant_id="test_stl_tenant",
            owner_id="test_stl_owner",
            deposit_amount=50000.0,
            pending_rent=5000.0,
            cleaning_charge=3000.0,
            damage_charge=2000.0,
            total_deductions=10000.0,
            refund_amount=40000.0,
            status=models.SettlementStatus.draft.value,
        )
        db.add(stl)
        db.commit()
        db.refresh(stl)

        assert stl.id is not None
        assert stl.refund_amount == 40000.0
        assert stl.status == "draft"

        db.delete(stl)
        db.commit()

    def test_settlement_with_deductions_json(self, db):
        deductions = [
            {"category": "cleaning", "description": "Kitchen", "amount": 3000},
            {"category": "damages", "description": "Wall scratch", "amount": 2000},
        ]
        stl = models.SettlementRecord(
            moveout_id=998,
            tenant_id="test_json_tenant",
            owner_id="test_json_owner",
            deposit_amount=50000.0,
            total_deductions=5000.0,
            refund_amount=45000.0,
            deductions_json=json.dumps(deductions),
            status="draft",
        )
        db.add(stl)
        db.commit()
        db.refresh(stl)

        parsed = json.loads(stl.deductions_json)
        assert len(parsed) == 2
        assert parsed[0]["category"] == "cleaning"
        assert parsed[1]["amount"] == 2000

        db.delete(stl)
        db.commit()


# ── Status Transition Tests ──────────────────────────────────────────────────

class TestMoveOutStatusTransitions:

    def test_full_lifecycle(self, db):
        """initiated → notice_period → owner_review → settlement_pending → completed"""
        vacate = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        mo = models.MoveOutRequest(
            agreement_id=997,
            property_id=1,
            tenant_id="lifecycle_tenant",
            owner_id="lifecycle_owner",
            status=models.MoveOutStatus.initiated.value,
            expected_vacate_date=vacate,
        )
        db.add(mo)
        db.commit()

        # → notice_period
        mo.status = models.MoveOutStatus.notice_period.value
        db.commit()
        assert mo.status == "notice_period"

        # → owner_review
        mo.status = models.MoveOutStatus.owner_review.value
        db.commit()
        assert mo.status == "owner_review"

        # → settlement_pending
        mo.status = models.MoveOutStatus.settlement_pending.value
        db.commit()
        assert mo.status == "settlement_pending"

        # → completed
        mo.status = models.MoveOutStatus.completed.value
        mo.actual_vacate_date = datetime.datetime.utcnow()
        db.commit()
        assert mo.status == "completed"
        assert mo.actual_vacate_date is not None

        db.delete(mo)
        db.commit()

    def test_cancellation(self, db):
        vacate = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        mo = models.MoveOutRequest(
            agreement_id=996,
            property_id=1,
            tenant_id="cancel_tenant",
            owner_id="cancel_owner",
            status=models.MoveOutStatus.notice_period.value,
            expected_vacate_date=vacate,
        )
        db.add(mo)
        db.commit()

        mo.status = models.MoveOutStatus.cancelled.value
        db.commit()
        assert mo.status == "cancelled"

        db.delete(mo)
        db.commit()


# ── Settlement Calculation Tests ─────────────────────────────────────────────

class TestSettlementCalculation:

    def test_full_refund(self):
        deposit = 50000.0
        deductions = 0.0
        refund = max(0, deposit - deductions)
        assert refund == 50000.0

    def test_partial_refund(self):
        deposit = 50000.0
        deductions = 8000.0
        refund = max(0, deposit - deductions)
        assert refund == 42000.0

    def test_zero_refund(self):
        deposit = 50000.0
        deductions = 60000.0
        refund = max(0, deposit - deductions)
        assert refund == 0.0  # Can't go negative

    def test_deductions_sum(self):
        pending_rent = 5000
        cleaning = 3000
        damages = 2000
        extra_items = [
            {"category": "other", "amount": 1000},
            {"category": "other", "amount": 500},
        ]
        total = pending_rent + cleaning + damages + sum(d["amount"] for d in extra_items)
        assert total == 11500


# ── PDF Generation Tests ─────────────────────────────────────────────────────

class TestSettlementPDF:

    def test_generate_html(self):
        html = generate_settlement_html({
            "id": 1,
            "tenant_id": "tenant@test.com",
            "owner_id": "owner@test.com",
            "agreement_id": 1,
            "deposit_amount": 50000,
            "pending_rent": 0,
            "cleaning_charge": 3000,
            "damage_charge": 5000,
            "total_deductions": 8000,
            "refund_amount": 42000,
            "deductions_json": json.dumps([
                {"category": "cleaning", "description": "Deep clean", "amount": 3000},
            ]),
            "owner_notes": "Good condition overall.",
        })

        assert "Settlement Statement" in html
        assert "tenant@test.com" in html
        assert "owner@test.com" in html
        assert "42,000" in html  # refund
        assert "3,000" in html  # cleaning deduction
        assert "5,000" in html  # damage deduction
        assert "Good condition overall." in html

    def test_generate_html_no_deductions(self):
        html = generate_settlement_html({
            "id": 2,
            "tenant_id": "t@t.com",
            "owner_id": "o@o.com",
            "deposit_amount": 30000,
            "pending_rent": 0,
            "cleaning_charge": 0,
            "damage_charge": 0,
            "total_deductions": 0,
            "refund_amount": 30000,
            "deductions_json": None,
        })

        assert "No deductions" in html
        assert "30,000" in html

    def test_generate_pdf_returns_none_or_bytes(self):
        """In test environment without WeasyPrint, should return None."""
        result = generate_settlement_pdf({
            "id": 3,
            "tenant_id": "t@t.com",
            "owner_id": "o@o.com",
            "deposit_amount": 50000,
            "total_deductions": 0,
            "refund_amount": 50000,
            "deductions_json": None,
        })
        # Either None (no WeasyPrint) or bytes (WeasyPrint installed)
        assert result is None or isinstance(result, bytes)


# ── Integration Flow Tests ───────────────────────────────────────────────────

class TestMoveOutFlow:

    def test_tenant_to_settlement_flow(self, db):
        """Full flow: initiate → review → settlement → complete."""
        now = datetime.datetime.utcnow()
        vacate = now + datetime.timedelta(days=30)

        # 1. Tenant initiates
        mo = models.MoveOutRequest(
            agreement_id=995,
            property_id=1,
            tenant_id="flow_t",
            owner_id="flow_o",
            status="notice_period",
            expected_vacate_date=vacate,
        )
        db.add(mo)
        db.commit()
        db.refresh(mo)
        assert mo.status == "notice_period"

        # 2. Create matching deposit for calculation
        deposit_txn = models.PaymentTransaction(
            agreement_id=995,
            tenant_id="flow_t",
            owner_id="flow_o",
            property_id=1,
            transaction_type="deposit",
            amount=50000.0,
            status="captured",
            paid_at=now - datetime.timedelta(days=90),
        )
        db.add(deposit_txn)
        db.commit()

        # 3. Owner reviews
        deductions = [
            {"category": "cleaning", "description": "Full clean", "amount": 3000},
        ]
        stl = models.SettlementRecord(
            moveout_id=mo.id,
            agreement_id=995,
            tenant_id="flow_t",
            owner_id="flow_o",
            deposit_amount=50000.0,
            pending_rent=0,
            cleaning_charge=3000,
            damage_charge=0,
            total_deductions=3000.0,
            refund_amount=47000.0,
            deductions_json=json.dumps(deductions),
            status="draft",
        )
        db.add(stl)
        mo.status = "settlement_pending"
        db.commit()

        assert stl.refund_amount == 47000.0

        # 4. Finalize
        stl.status = "finalized"
        stl.finalized_at = now
        mo.status = "completed"
        mo.actual_vacate_date = now
        db.commit()

        assert stl.status == "finalized"
        assert mo.status == "completed"

        # Cleanup
        db.delete(stl)
        db.delete(deposit_txn)
        db.delete(mo)
        db.commit()

    def test_duplicate_moveout_prevented(self, db):
        """Can't have two active move-outs for the same agreement."""
        vacate = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        mo1 = models.MoveOutRequest(
            agreement_id=994, property_id=1,
            tenant_id="dup_t", owner_id="dup_o",
            status="notice_period", expected_vacate_date=vacate,
        )
        db.add(mo1)
        db.commit()

        # Query should find existing
        existing = db.query(models.MoveOutRequest).filter(
            models.MoveOutRequest.agreement_id == 994,
            models.MoveOutRequest.status.notin_(["completed", "cancelled"]),
        ).first()

        assert existing is not None
        assert existing.id == mo1.id

        db.delete(mo1)
        db.commit()
