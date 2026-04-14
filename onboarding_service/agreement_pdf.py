"""
Rentora — Digital Agreement PDF Generator
"""

import datetime


def generate_agreement_html(agreement) -> str:
    """Generate branded rental agreement HTML."""
    now = datetime.datetime.utcnow()

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rental Agreement - Rentora</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; margin: 0; padding: 0; font-size: 13px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #0A3D62, #1B6CA8); color: #fff; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.8; }}
        .doc-id {{ float: right; font-size: 12px; background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 4px; }}
        .body {{ padding: 30px; }}
        .section {{ margin-bottom: 24px; }}
        .section h2 {{ color: #0A3D62; font-size: 16px; border-bottom: 2px solid #e8e8e8; padding-bottom: 8px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .info-item {{ background: #f8f9fa; padding: 12px; border-radius: 6px; }}
        .info-item label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
        .info-item p {{ margin: 4px 0 0; font-weight: 600; }}
        .terms {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 16px 0; }}
        .terms li {{ margin: 6px 0; }}
        .signature-box {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 40px; }}
        .sig {{ border-top: 2px solid #333; padding-top: 10px; text-align: center; }}
        .sig .role {{ font-weight: 700; color: #0A3D62; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 16px; border-top: 1px solid #eee; font-size: 11px; color: #999; }}
        .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="doc-id">AGR-{agreement.id:04d}</span>
        <h1>Rental Agreement</h1>
        <p>Rentora — Your Rental Operating System</p>
    </div>
    <div class="body">
        <div class="section">
            <h2>Agreement Details</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>Agreement ID</label>
                    <p>AGR-{agreement.id:04d}</p>
                </div>
                <div class="info-item">
                    <label>Property ID</label>
                    <p>#{agreement.property_id}</p>
                </div>
                <div class="info-item">
                    <label>Start Date</label>
                    <p>{agreement.start_date or 'TBD'}</p>
                </div>
                <div class="info-item">
                    <label>End Date</label>
                    <p>{agreement.end_date or 'TBD'}</p>
                </div>
                <div class="info-item">
                    <label>Monthly Rent</label>
                    <p>Rs.{agreement.monthly_rent:,.0f}</p>
                </div>
                <div class="info-item">
                    <label>Security Deposit</label>
                    <p>Rs.{agreement.security_deposit:,.0f}</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Parties</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>Tenant (Lessee)</label>
                    <p>{agreement.tenant_id}</p>
                </div>
                <div class="info-item">
                    <label>Owner (Lessor)</label>
                    <p>{agreement.owner_id}</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Terms & Conditions</h2>
            <div class="terms">
                <ol>
                    <li>The tenant shall pay the monthly rent on or before the 5th of each month.</li>
                    <li>The security deposit of Rs.{agreement.security_deposit:,.0f} shall be refunded upon vacating, subject to deductions for damages.</li>
                    <li>The notice period for termination is {agreement.notice_period_days} days.</li>
                    <li>The tenant shall maintain the property in good condition and shall not make structural changes without written consent.</li>
                    <li>The owner shall ensure all essential services (water, electricity) are in working order.</li>
                    <li>This agreement is governed by the laws of India and subject to local rent control regulations.</li>
                    <li>In case of disputes, both parties agree to mediation before legal proceedings.</li>
                </ol>
            </div>
        </div>

        <div class="section">
            <h2>Signatures</h2>
            <div class="signature-box">
                <div class="sig">
                    <p class="role">Tenant</p>
                    <p>{agreement.tenant_id}</p>
                    <p style="font-size:11px;color:#888;">{'Signed at: ' + agreement.tenant_signed_at.strftime('%B %d, %Y') if agreement.tenant_signed_at else 'Pending Signature'}</p>
                </div>
                <div class="sig">
                    <p class="role">Owner</p>
                    <p>{agreement.owner_id}</p>
                    <p style="font-size:11px;color:#888;">{'Signed at: ' + agreement.owner_signed_at.strftime('%B %d, %Y') if agreement.owner_signed_at else 'Pending Signature'}</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>This is a digitally generated agreement from Rentora.</p>
            <p>Document Hash: {agreement.document_hash or 'N/A'}</p>
            <p>Generated on {now.strftime('%B %d, %Y at %I:%M %p UTC')}</p>
        </div>
    </div>
</body>
</html>"""
