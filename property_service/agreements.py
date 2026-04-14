import os
from weasyprint import HTML
import hashlib
import datetime
from sqlalchemy.orm import Session
from . import models

class AgreementService:
    UPLOAD_DIR = "uploads/agreements"
    
    @staticmethod
    def generate_pdf(agreement_id: int, property_title: str, tenant_name: str, owner_name: str, rent: float, db: Session):
        # 1. Simple HTML Template for Rental Agreement
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica', sans-serif; padding: 50px; color: #333; }}
                h1 {{ color: #0A3D62; text-align: center; }}
                .section {{ margin-bottom: 20px; }}
                .label {{ font-weight: bold; }}
                .footer {{ margin-top: 100px; border-top: 1px solid #ccc; padding-top: 20px; text-align: center; font-size: 10px; }}
            </style>
        </head>
        <body>
            <h1>RESIDENTIAL RENTAL AGREEMENT</h1>
            <div class="section">
                <p>This agreement is entered into on <span class="label">{datetime.date.today()}</span></p>
                <p>BETWEEN: <span class="label">{owner_name}</span> (the 'Owner')</p>
                <p>AND: <span class="label">{tenant_name}</span> (the 'Tenant')</p>
            </div>
            <div class="section">
                <h3>1. PROPERTY</h3>
                <p>The Owner agrees to rent the property known as <span class="label">{property_title}</span> to the Tenant.</p>
            </div>
            <div class="section">
                <h3>2. RENT</h3>
                <p>The monthly rent shall be <span class="label">INR {rent}</span>, payable on the 1st of each month.</p>
            </div>
            <div class="section">
                <h3>3. TERMS</h3>
                <p>This is a legally binding digital agreement generated via Rentora. Both parties agree to the digital signature process.</p>
            </div>
            <div class="footer">
                Agreement ID: {agreement_id} | Security Hash: [PENDING SIGNATURE]
            </div>
        </body>
        </html>
        """
        
        # 2. Generate PDF
        file_name = f"agreement_{agreement_id}.pdf"
        file_path = os.path.join(AgreementService.UPLOAD_DIR, file_name)
        
        # Ensure dir exists
        os.makedirs(AgreementService.UPLOAD_DIR, exist_ok=True)
        
        HTML(string=html_content).write_pdf(file_path)
        
        # 3. Calculate Hash for integrity
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            
        # Update Agreement record
        agreement = db.query(models.RentalAgreement).filter(models.RentalAgreement.id == agreement_id).first()
        if agreement:
            agreement.pdf_url = f"/uploads/agreements/{file_name}"
            agreement.document_hash = file_hash
            db.commit()
            
        return file_path, file_hash

class ESignService:
    """Mock integration for SignNow/DocuSign"""
    
    @staticmethod
    def get_signing_url(agreement_id: int):
        # In production, this would call e.g. signnow.Document.create_invite()
        # Mocking a redirect to a signature pad UI
        return f"https://mock-esign.rentora.com/sign/{agreement_id}?callback=rentora.com/verify"

    @staticmethod
    def verify_signature(document_id: str):
        # Mock metadata
        return {
            "signed_at": datetime.datetime.utcnow(),
            "ip_address": "192.168.1.45",
            "audit_log": f"Signature verified for doc {document_id}"
        }
