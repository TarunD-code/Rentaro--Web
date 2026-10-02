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

import shared_storage

def generate_pdf_report(owner_id: str, metrics: list, report_type: str) -> Optional[str]:
    """Generate PDF, upload to centralized storage, and return the access URL."""
    html = generate_report_html(owner_id, metrics, report_type)
    
    temp_dir = "temp_reports"
    os.makedirs(temp_dir, exist_ok=True)
        
    filename = f"report_{owner_id}_{report_type}_{int(datetime.datetime.now().timestamp())}.pdf"
    filepath = os.path.join(temp_dir, filename)
    file_key = f"reports/{filename}"
    
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(filepath)
        
        # Upload using centralized storage manager
        with open(filepath, "rb") as f:
            public_url = shared_storage.upload_file(f, file_key, "application/pdf")
            
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return public_url
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        # Fallback: Save HTML temporarily and upload
        html_filename = filename.replace(".pdf", ".html")
        html_path = os.path.join(temp_dir, html_filename)
        html_key = f"reports/{html_filename}"
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            with open(html_path, "rb") as f:
                public_url = shared_storage.upload_file(f, html_key, "text/html")
            if os.path.exists(html_path):
                os.remove(html_path)
            return public_url
        except Exception as ex:
            logger.error(f"Fallback HTML report generation failed: {ex}")
            return None

