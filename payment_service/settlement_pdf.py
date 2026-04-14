"""
Settlement PDF Generator

Generates settlement PDF documents using WeasyPrint (if available).
Falls back to returning HTML content if WeasyPrint is not installed.
"""

import logging
import datetime
import json
from typing import Optional

logger = logging.getLogger("payment_service.settlement_pdf")


def generate_settlement_html(settlement_data: dict) -> str:
    """Generate settlement HTML from settlement data."""
    deductions = []
    if settlement_data.get("deductions_json"):
        try:
            deductions = json.loads(settlement_data["deductions_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    deductions_rows = ""
    for i, d in enumerate(deductions, 1):
        deductions_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{d.get('category', '').replace('_', ' ').title()}</td>
            <td>{d.get('description', '-')}</td>
            <td class="amount">Rs.{d.get('amount', 0):,.0f}</td>
        </tr>"""

    if not deductions_rows:
        deductions_rows = '<tr><td colspan="4" style="text-align:center;color:#888;">No deductions</td></tr>'

    refund = settlement_data.get("refund_amount", 0)
    refund_color = "#27ae60" if refund > 0 else "#e74c3c"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Settlement Statement - Rentora</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; margin: 0; padding: 0; font-size: 13px; }}
        .header {{ background: linear-gradient(135deg, #0A3D62, #1B6CA8); color: #fff; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 22px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.8; font-size: 12px; }}
        .settlement-id {{ float: right; font-size: 14px; font-weight: 700; background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 4px; }}
        .body {{ padding: 30px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
        .info-box {{ background: #f8f9fa; padding: 16px; border-radius: 6px; }}
        .info-box label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
        .info-box p {{ margin: 4px 0 0; font-weight: 600; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th {{ background: #f0f0f0; text-align: left; padding: 10px 12px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        .amount {{ text-align: right; font-weight: 600; }}
        .summary {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin-top: 24px; }}
        .summary-row {{ display: flex; justify-content: space-between; padding: 8px 0; }}
        .summary-row.total {{ border-top: 2px solid #333; font-size: 16px; font-weight: 700; padding-top: 12px; margin-top: 8px; }}
        .refund-box {{ background: {refund_color}; color: #fff; padding: 20px; border-radius: 8px; text-align: center; margin-top: 20px; }}
        .refund-box .label {{ font-size: 12px; opacity: 0.8; }}
        .refund-box .amount {{ font-size: 28px; font-weight: 800; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 11px; color: #999; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="settlement-id">STL-{settlement_data.get('id', 0):06d}</span>
        <h1>Settlement Statement</h1>
        <p>Rentora - Your Rental Operating System</p>
    </div>
    <div class="body">
        <div class="info-grid">
            <div class="info-box">
                <label>Tenant</label>
                <p>{settlement_data.get('tenant_id', '-')}</p>
            </div>
            <div class="info-box">
                <label>Owner</label>
                <p>{settlement_data.get('owner_id', '-')}</p>
            </div>
            <div class="info-box">
                <label>Agreement ID</label>
                <p>#{settlement_data.get('agreement_id', '-')}</p>
            </div>
            <div class="info-box">
                <label>Settlement Date</label>
                <p>{datetime.datetime.utcnow().strftime('%B %d, %Y')}</p>
            </div>
        </div>

        <h3>Deductions Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th style="text-align:right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {deductions_rows}
            </tbody>
        </table>

        <div class="summary">
            <div class="summary-row">
                <span>Security Deposit</span>
                <span>Rs.{settlement_data.get('deposit_amount', 0):,.0f}</span>
            </div>
            <div class="summary-row">
                <span>Pending Rent</span>
                <span style="color:#e74c3c;">- Rs.{settlement_data.get('pending_rent', 0):,.0f}</span>
            </div>
            <div class="summary-row">
                <span>Cleaning Charges</span>
                <span style="color:#e74c3c;">- Rs.{settlement_data.get('cleaning_charge', 0):,.0f}</span>
            </div>
            <div class="summary-row">
                <span>Damage Charges</span>
                <span style="color:#e74c3c;">- Rs.{settlement_data.get('damage_charge', 0):,.0f}</span>
            </div>
            <div class="summary-row total">
                <span>{'Refund to Tenant' if refund >= 0 else 'Amount Due from Tenant'}</span>
                <span style="color:{refund_color};">Rs.{abs(refund):,.0f}</span>
            </div>
        </div>

        <div class="refund-box">
            <div class="label">{'REFUND AMOUNT' if refund >= 0 else 'AMOUNT DUE'}</div>
            <div class="amount">Rs.{abs(refund):,.0f}</div>
        </div>

        {f'<div style="margin-top:20px;"><h3>Owner Notes</h3><p>{settlement_data.get("owner_notes", "")}</p></div>' if settlement_data.get("owner_notes") else ''}

        <div class="footer">
            <p>This is a computer-generated settlement statement from Rentora.</p>
            <p>Generated on {datetime.datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
        </div>
    </div>
</body>
</html>"""
    return html


def generate_settlement_pdf(settlement_data: dict) -> Optional[bytes]:
    """Generate settlement PDF. Returns bytes or None if WeasyPrint unavailable."""
    html = generate_settlement_html(settlement_data)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        logger.info(f"Settlement PDF generated for STL-{settlement_data.get('id', 0):06d}")
        return pdf_bytes
    except ImportError:
        logger.warning("WeasyPrint not available - returning None (HTML fallback)")
        return None
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None
