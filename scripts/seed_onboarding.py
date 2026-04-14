"""
Seed Onboarding Demo Data — Sprint 13

Creates sample onboarding records, KYC documents, agreements, and signatures.
Run: python -m scripts.seed_onboarding
"""

import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onboarding_service.database import SessionLocal, engine
from onboarding_service import models


def seed():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.datetime.utcnow()

    existing = db.query(models.OnboardingRecord).first()
    if existing:
        print("Onboarding data already seeded. Skipping.")
        db.close()
        return

    print("Seeding onboarding data...")

    # 1. Completed onboarding with verified KYC
    ob1 = models.OnboardingRecord(
        tenant_id="admin@rentora.com", property_id=1,
        full_name="Tarun D", email="admin@rentora.com", phone="+91-9876543210",
        date_of_birth="1998-05-15", age=28, permanent_address="123 MG Road, Bangalore",
        emergency_contact="+91-9876543211", occupation="Software Engineer", employer="TechCorp",
        status="completed", kyc_status="verified",
        verified_by="admin@rentora.com", verified_at=now - datetime.timedelta(days=20),
        created_at=now - datetime.timedelta(days=25),
    )
    db.add(ob1)
    db.flush()
    print(f"  Added onboarding #{ob1.id} (completed, verified)")

    # KYC for ob1
    kyc1 = models.OnboardingKYC(
        onboarding_id=ob1.id, tenant_id="admin@rentora.com",
        document_type="aadhaar", document_number="XXXX4321",
        file_url="/uploads/kyc/aadhaar_1.pdf", status="verified",
        uploaded_at=now - datetime.timedelta(days=24),
    )
    kyc2 = models.OnboardingKYC(
        onboarding_id=ob1.id, tenant_id="admin@rentora.com",
        document_type="pan", document_number="XXXX1234F",
        file_url="/uploads/kyc/pan_1.pdf", status="verified",
        uploaded_at=now - datetime.timedelta(days=24),
    )
    db.add_all([kyc1, kyc2])
    print(f"  Added KYC: Aadhaar + PAN for onboarding #{ob1.id}")

    # 2. Pending onboarding (KYC submitted)
    ob2 = models.OnboardingRecord(
        tenant_id="tenant2@rentora.com", property_id=2,
        full_name="Priya Sharma", email="tenant2@rentora.com", phone="+91-9123456789",
        occupation="Marketing Manager", employer="MediaInc",
        status="kyc_submitted", kyc_status="pending",
        created_at=now - datetime.timedelta(days=3),
    )
    db.add(ob2)
    db.flush()
    print(f"  Added onboarding #{ob2.id} (kyc_submitted, pending)")

    kyc3 = models.OnboardingKYC(
        onboarding_id=ob2.id, tenant_id="tenant2@rentora.com",
        document_type="passport", document_number="XXXX5678",
        file_url="/uploads/kyc/passport_2.pdf", status="pending",
        uploaded_at=now - datetime.timedelta(days=2),
    )
    db.add(kyc3)

    # 3. Fully signed agreement
    ag1 = models.DigitalAgreement(
        onboarding_id=ob1.id, property_id=1,
        tenant_id="admin@rentora.com", owner_id="owner@rentora.com",
        start_date="2026-01-01", end_date="2026-12-31",
        monthly_rent=15000.0, security_deposit=45000.0,
        notice_period_days=30, document_hash="a1b2c3d4e5f6",
        pdf_url="/onboarding/agreements/1/pdf",
        status="fully_signed",
        tenant_signed_at=now - datetime.timedelta(days=18),
        owner_signed_at=now - datetime.timedelta(days=17),
        fully_signed_at=now - datetime.timedelta(days=17),
        created_at=now - datetime.timedelta(days=19),
    )
    db.add(ag1)
    db.flush()
    print(f"  Added agreement #{ag1.id} (fully_signed)")

    # Signatures for ag1
    sig1 = models.SignatureRecord(
        agreement_id=ag1.id, signer_id="admin@rentora.com", signer_role="tenant",
        sign_link="/onboarding/agreements/1/sign/abc123",
        status="signed", signed_at=now - datetime.timedelta(days=18),
    )
    sig2 = models.SignatureRecord(
        agreement_id=ag1.id, signer_id="owner@rentora.com", signer_role="owner",
        sign_link="/onboarding/agreements/1/sign/def456",
        status="signed", signed_at=now - datetime.timedelta(days=17),
    )
    db.add_all([sig1, sig2])

    # 4. Draft agreement (pending signatures)
    ag2 = models.DigitalAgreement(
        property_id=2,
        tenant_id="tenant2@rentora.com", owner_id="owner@rentora.com",
        start_date="2026-05-01", end_date="2027-04-30",
        monthly_rent=20000.0, security_deposit=60000.0,
        notice_period_days=30, document_hash="f6e5d4c3b2a1",
        pdf_url="/onboarding/agreements/2/pdf",
        status="generated",
        created_at=now - datetime.timedelta(days=1),
    )
    db.add(ag2)
    db.flush()
    print(f"  Added agreement #{ag2.id} (generated, awaiting signatures)")

    db.commit()
    db.close()
    print("[OK] Onboarding seed complete!")


if __name__ == "__main__":
    seed()
