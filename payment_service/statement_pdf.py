"""
Statement PDF Generator

Generates monthly owner statements using WeasyPrint (if available).
Falls back to returning HTML content if WeasyPrint is not installed.
"""

import logging
import datetime
import json
from typing import Optional, List

logger = logging.getLogger("payment_service.statement_pdf")


def generate_statement_html(statement_data: dict) -> str:
    """Generate statement HTML from monthly ledger data."""
    entries = statement_data.get("entries", [])
    
    entries_rows = ""
    for i, e in enumerate(entries, 1):
        amount_val = e.amount
        color = "#27ae60" if amount_val > 0 else "#e74c3c"
        entries_rows += f"""
        <tr>
            <td>{datetime.datetime.fromisoformat(str(e.created_at)).strftime('%b %d, %Y')}</td>
            <td>{e.entry_type.replace('_', ' ').title()}</td>
            <td>{e.description or '-'}</td>
            <td class="amount" style="color:{color}">Rs.{amount_val:,.2f}</td>
        </tr>"""

    if not entries_rows:
        entries_rows = '<tr><td colspan="4" style="text-align:center;color:#888;">No transactions this month</td></tr>'

    total_credits = sum(e.amount for e in entries if e.amount > 0)
    total_debits = sum(e.amount for e in entries if e.amount < 0)
    net_change = total_credits + total_debits
    net_color = "#27ae60" if net_change >= 0 else "#e74c3c"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Statement - Rentora</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; margin: 0; padding: 0; font-size: 13px; }}
        .header {{ background: linear-gradient(135deg, #0A3D62, #1B6CA8); color: #fff; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 22px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.8; font-size: 12px; }}
        .statement-month {{ float: right; font-size: 14px; font-weight: 700; background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 4px; }}
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
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 11px; color: #999; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="statement-month">{statement_data.get('month', 'MM-YYYY')}</span>
        <h1>Account Statement</h1>
        <p>Rentora Property Management</p>
    </div>
    <div class="body">
        <div class="info-grid">
            <div class="info-box">
                <label>Account Owner</label>
                <p>{statement_data.get('owner_id', '-')}</p>
            </div>
            <div class="info-box">
                <label>Statement Period</label>
                <p>{statement_data.get('month', 'MM-YYYY')}</p>
            </div>
        </div>

        <h3>Ledger Transactions</h3>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th style="text-align:right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {entries_rows}
            </tbody>
        </table>

        <div class="summary">
            <div class="summary-row">
                <span>Total Credits (Incoming Rent)</span>
                <span style="color:#27ae60;">Rs.{total_credits:,.2f}</span>
            </div>
            <div class="summary-row">
                <span>Total Debits (Fees, Withdrawals)</span>
                <span style="color:#e74c3c;">Rs.{abs(total_debits):,.2f}</span>
            </div>
            <div class="summary-row total">
                <span>Net Change for Period</span>
                <span style="color:{net_color};">Rs.{net_change:,.2f}</span>
            </div>
        </div>

        <div class="footer">
            <p>This is a computer-generated statement from Rentora.</p>
            <p>Generated on {datetime.datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
        </div>
    </div>
</body>
</html>"""
    return html


def generate_statement_pdf(statement_data: dict) -> Optional[bytes]:
    """Generate statement PDF. Returns bytes or None if WeasyPrint unavailable."""
    html = generate_statement_html(statement_data)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        logger.info(f"Statement PDF generated for owner {statement_data.get('owner_id')} - {statement_data.get('month')}")
        return pdf_bytes
    except ImportError:
        logger.warning("WeasyPrint not available - returning None (HTML fallback)")
        return None
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None
