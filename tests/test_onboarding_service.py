"""
Unit & Integration Tests for Onboarding Service — Sprint 13

Run: python -m pytest tests/test_onboarding_service.py -v
"""

import sys, os, datetime
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onboarding_service.database import SessionLocal, engine, Base
from onboarding_service import models


@pytest.fixture(scope="module")
def db():
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# ── Enum Tests ───────────────────────────────────────────────────────────────

class TestEnums:
    def test_onboarding_statuses(self):
        assert models.OnboardingStatus.initiated.value == "initiated"
        assert models.OnboardingStatus.documents_pending.value == "documents_pending"
        assert models.OnboardingStatus.kyc_submitted.value == "kyc_submitted"
        assert models.OnboardingStatus.kyc_verified.value == "kyc_verified"
        assert models.OnboardingStatus.completed.value == "completed"

    def test_kyc_document_types(self):
        assert models.KYCDocumentType.aadhaar.value == "aadhaar"
        assert models.KYCDocumentType.pan.value == "pan"
        assert models.KYCDocumentType.passport.value == "passport"
        assert models.KYCDocumentType.voter_id.value == "voter_id"
        assert models.KYCDocumentType.driving_licence.value == "driving_licence"

    def test_agreement_statuses(self):
        assert models.AgreementStatus.draft.value == "draft"
        assert models.AgreementStatus.generated.value == "generated"
        assert models.AgreementStatus.sent_for_signing.value == "sent_for_signing"
        assert models.AgreementStatus.fully_signed.value == "fully_signed"
        assert models.AgreementStatus.active.value == "active"

    def test_signature_statuses(self):
        assert models.SignatureStatus.pending.value == "pending"
        assert models.SignatureStatus.sent.value == "sent"
        assert models.SignatureStatus.signed.value == "signed"
        assert models.SignatureStatus.declined.value == "declined"


# ── Model CRUD Tests ────────────────────────────────────────────────────────

class TestOnboardingModel:

    def test_create_onboarding(self, db):
        rec = models.OnboardingRecord(
            tenant_id="test_ob_tenant", full_name="Test User",
            email="test@test.com", phone="+91-1234567890",
            occupation="Engineer", status="initiated",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        assert rec.id is not None
        assert rec.tenant_id == "test_ob_tenant"
        assert rec.status == "initiated"
        assert rec.kyc_status == "pending"

        db.delete(rec)
        db.commit()

    def test_onboarding_with_full_details(self, db):
        rec = models.OnboardingRecord(
            tenant_id="full_details_t", property_id=99,
            full_name="Full Details User", email="full@test.com", phone="+91-9999999999",
            date_of_birth="1995-01-15", age=31,
            permanent_address="456 Park Avenue, Mumbai",
            emergency_contact="+91-8888888888",
            occupation="Doctor", employer="City Hospital",
            status="documents_pending",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        assert rec.property_id == 99
        assert rec.age == 31
        assert rec.employer == "City Hospital"

        db.delete(rec)
        db.commit()


class TestKYCModel:

    def test_create_kyc(self, db):
        kyc = models.OnboardingKYC(
            onboarding_id=999, tenant_id="kyc_test_t",
            document_type="aadhaar", document_number="XXXX1234",
            file_url="/uploads/kyc/test.pdf", status="pending",
        )
        db.add(kyc)
        db.commit()
        db.refresh(kyc)

        assert kyc.id is not None
        assert kyc.document_type == "aadhaar"
        assert kyc.document_number == "XXXX1234"

        db.delete(kyc)
        db.commit()

    def test_kyc_verification(self, db):
        kyc = models.OnboardingKYC(
            onboarding_id=998, tenant_id="kyc_verify_t",
            document_type="pan", document_number="XXXX5678F",
            status="pending",
        )
        db.add(kyc)
        db.commit()

        kyc.status = "verified"
        db.commit()
        assert kyc.status == "verified"

        db.delete(kyc)
        db.commit()

    def test_kyc_rejection(self, db):
        kyc = models.OnboardingKYC(
            onboarding_id=997, tenant_id="kyc_reject_t",
            document_type="passport", status="pending",
        )
        db.add(kyc)
        db.commit()

        kyc.status = "rejected"
        kyc.rejection_reason = "Document is blurry"
        db.commit()
        assert kyc.status == "rejected"
        assert kyc.rejection_reason == "Document is blurry"

        db.delete(kyc)
        db.commit()


class TestAgreementModel:

    def test_create_agreement(self, db):
        ag = models.DigitalAgreement(
            property_id=1, tenant_id="ag_t", owner_id="ag_o",
            start_date="2026-05-01", end_date="2027-04-30",
            monthly_rent=15000.0, security_deposit=45000.0,
            status="draft",
        )
        db.add(ag)
        db.commit()
        db.refresh(ag)

        assert ag.id is not None
        assert ag.monthly_rent == 15000.0
        assert ag.status == "draft"

        db.delete(ag)
        db.commit()

    def test_agreement_pdf(self, db):
        from onboarding_service.agreement_pdf import generate_agreement_html

        ag = models.DigitalAgreement(
            property_id=1, tenant_id="pdf_t", owner_id="pdf_o",
            start_date="2026-06-01", end_date="2027-05-31",
            monthly_rent=20000.0, security_deposit=60000.0,
            notice_period_days=30, document_hash="test123",
            status="generated",
        )
        db.add(ag)
        db.commit()
        db.refresh(ag)

        html = generate_agreement_html(ag)
        assert "Rental Agreement" in html
        assert "Rs.20,000" in html
        assert "Rs.60,000" in html
        assert "pdf_t" in html
        assert "pdf_o" in html
        assert "test123" in html

        db.delete(ag)
        db.commit()


class TestSignatureModel:

    def test_create_signature(self, db):
        sig = models.SignatureRecord(
            agreement_id=999, signer_id="sig_t", signer_role="tenant",
            sign_link="/sign/abc123", status="sent",
        )
        db.add(sig)
        db.commit()
        db.refresh(sig)

        assert sig.id is not None
        assert sig.signer_role == "tenant"
        assert sig.status == "sent"

        db.delete(sig)
        db.commit()


# ── Flow Tests ────────────────────────────────────────────────────────────────

class TestOnboardingFlow:

    def test_full_onboarding_lifecycle(self, db):
        """initiated → documents_pending → kyc_submitted → kyc_verified → completed"""
        rec = models.OnboardingRecord(
            tenant_id="lifecycle_ob_t", full_name="Lifecycle User",
            email="lifecycle@test.com", phone="+91-1111111111",
            status="initiated",
        )
        db.add(rec)
        db.commit()

        for status in ["documents_pending", "kyc_submitted", "kyc_verified", "completed"]:
            rec.status = status
            if status == "kyc_verified":
                rec.kyc_status = "verified"
                rec.verified_at = datetime.datetime.utcnow()
            db.commit()
            assert rec.status == status

        assert rec.kyc_status == "verified"
        assert rec.verified_at is not None

        db.delete(rec)
        db.commit()

    def test_agreement_signing_flow(self, db):
        """draft → generated → sent_for_signing → tenant_signed → fully_signed"""
        ag = models.DigitalAgreement(
            property_id=1, tenant_id="sign_flow_t", owner_id="sign_flow_o",
            monthly_rent=18000.0, security_deposit=54000.0, status="draft",
        )
        db.add(ag)
        db.commit()

        ag.status = "generated"
        ag.pdf_url = "/agreements/test/pdf"
        db.commit()

        ag.status = "sent_for_signing"
        ag.docusign_envelope_id = "ENV-TEST123"
        db.commit()

        # Tenant signs
        sig_t = models.SignatureRecord(
            agreement_id=ag.id, signer_id="sign_flow_t", signer_role="tenant",
            status="signed", signed_at=datetime.datetime.utcnow(),
        )
        db.add(sig_t)
        ag.status = "tenant_signed"
        ag.tenant_signed_at = datetime.datetime.utcnow()
        db.commit()

        # Owner signs
        sig_o = models.SignatureRecord(
            agreement_id=ag.id, signer_id="sign_flow_o", signer_role="owner",
            status="signed", signed_at=datetime.datetime.utcnow(),
        )
        db.add(sig_o)
        ag.status = "fully_signed"
        ag.owner_signed_at = datetime.datetime.utcnow()
        ag.fully_signed_at = datetime.datetime.utcnow()
        db.commit()

        assert ag.status == "fully_signed"
        assert ag.tenant_signed_at is not None
        assert ag.owner_signed_at is not None
        assert ag.fully_signed_at is not None

        db.delete(sig_t)
        db.delete(sig_o)
        db.delete(ag)
        db.commit()

    def test_onboarding_to_agreement_flow(self, db):
        """Full flow: onboarding → KYC → agreement → signatures."""
        # 1. Onboarding
        ob = models.OnboardingRecord(
            tenant_id="e2e_t", full_name="E2E User",
            email="e2e@test.com", phone="+91-2222222222",
            status="documents_pending",
        )
        db.add(ob)
        db.commit()
        db.refresh(ob)

        # 2. KYC
        kyc = models.OnboardingKYC(
            onboarding_id=ob.id, tenant_id="e2e_t",
            document_type="aadhaar", document_number="XXXX9999", status="verified",
        )
        db.add(kyc)
        ob.status = "kyc_verified"
        ob.kyc_status = "verified"
        db.commit()

        # 3. Agreement
        ag = models.DigitalAgreement(
            onboarding_id=ob.id, property_id=1,
            tenant_id="e2e_t", owner_id="e2e_o",
            monthly_rent=12000.0, security_deposit=36000.0,
            status="fully_signed",
        )
        db.add(ag)
        ob.agreement_id = ag.id
        ob.status = "completed"
        db.commit()

        assert ob.status == "completed"
        assert ag.status == "fully_signed"

        db.delete(kyc)
        db.delete(ag)
        db.delete(ob)
        db.commit()
