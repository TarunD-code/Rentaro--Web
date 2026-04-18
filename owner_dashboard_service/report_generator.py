import datetime
import os
from typing import Optional
import logging

logger = logging.getLogger("owner_dashboard.reports")

def generate_report_html(owner_id: str, metrics: list, report_type: str) -> str:
    """Generate HTML for owner reports."""
    rows = ""
    total_rev = 0
    for m in metrics:
        rows += f"""
        <tr>
            <td>{m.id}</td>
            <td>{m.property_id}</td>
            <td>{m.period_start.strftime('%B %Y')}</td>
            <td>₹{m.revenue_total:,.2f}</td>
            <td>{'Occupied' if m.occupancy_count > 0 else 'Vacant'}</td>
            <td>₹{m.pending_rent_total:,.2f}</td>
        </tr>
        """
        total_rev += m.revenue_total

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; padding: 40px; color: #333; }}
            .header {{ border-bottom: 2px solid #1a73e8; padding-bottom: 20px; margin-bottom: 30px; }}
            .title {{ font-size: 24px; font-weight: bold; color: #1a73e8; }}
            .subtitle {{ color: #666; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #eee; padding: 12px; text-align: left; }}
            th {{ background: #f8f9fa; color: #5f6368; text-transform: uppercase; font-size: 11px; }}
            .total-section {{ margin-top: 30px; text-align: right; font-size: 18px; font-weight: bold; }}
            .footer {{ margin-top: 50px; font-size: 10px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">{report_type.upper()} REPORT</div>
            <div class="subtitle">Rentora Owner Premium Services | Report for Owner ID: {owner_id}</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Property ID</th>
                    <th>Period</th>
                    <th>Revenue</th>
                    <th>Status</th>
                    <th>Pending</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <div class="total-section">
            Total Revenue: ₹{total_rev:,.2f}
        </div>
        <div class="footer">
            Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Rentora Confidential
        </div>
    </body>
    </html>
    """
    return html

def generate_pdf_report(owner_id: str, metrics: list, report_type: str) -> Optional[str]:
    """Generate PDF and save locally. Returns the relative file path."""
    html = generate_report_html(owner_id, metrics, report_type)
    
    # Ensure directory exists
    report_dir = "uploads/reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    filename = f"report_{owner_id}_{report_type}_{int(datetime.datetime.now().timestamp())}.pdf"
    filepath = os.path.join(report_dir, filename)
    
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(filepath)
        return f"/static/reports/{filename}"
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        # Fallback: Save HTML for debugging/alternative
        html_path = filepath.replace(".pdf", ".html")
        with open(html_path, "w") as f:
            f.write(html)
        return f"/static/reports/{filename.replace('.pdf', '.html')}"
