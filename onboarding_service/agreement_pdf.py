"""
Rentora — Karnataka Leave & License Agreement Generator
========================================================
Produces a legally structured 11-month Leave & License agreement
HTML document conforming to standard Bengaluru / Karnataka norms:

  • 11-month term (avoids Rent Control Act applicability)
  • Security deposit: 10–11 months rent (configurable)
  • 2-month notice period
  • 1-month painting deduction clause on exit
  • Monthly rent payable on or before the 5th
  • Governing law: Karnataka Rent Act 1999 + Indian Contract Act 1872

The generated HTML is served via the /agreements/{id}/pdf endpoint
and is also the source document for the canvas e-signature overlay.
"""

import datetime


# ---------------------------------------------------------------------------
# Bengaluru-specific standard clauses
# ---------------------------------------------------------------------------

_STANDARD_CLAUSES = [
    (
        "Rent Payment Schedule",
        "The Licensee shall pay the monthly License Fee of Rs.{monthly_rent}/- on or before "
        "the 5th day of each calendar month. A late payment charge of 5% per month shall "
        "be levied on amounts outstanding beyond the 7th of any month.",
    ),
    (
        "Security Deposit",
        "The Licensee has paid a refundable Security Deposit of Rs.{security_deposit}/- to "
        "the Licensor. This deposit shall be refunded within 15 days of the Licensee vacating "
        "the premises, after deducting legitimate outstanding dues.",
    ),
    (
        "Notice Period",
        "Either party may terminate this agreement by providing a written notice of "
        "{notice_period_days} days. In the absence of such notice, the Licensee shall pay "
        "rent in lieu of the unserved notice period.",
    ),
    (
        "Painting Deduction on Exit (Bengaluru Standard)",
        "Upon vacation of the premises, the Licensor is entitled to deduct an amount "
        "equivalent to one month's License Fee (Rs.{monthly_rent}/-) from the Security Deposit "
        "towards repainting and restoration of the premises to its original condition, "
        "irrespective of the duration of occupancy. This is a standard Bengaluru market norm "
        "acknowledged and accepted by the Licensee.",
    ),
    (
        "Maintenance and Repairs",
        "Day-to-day minor repairs up to Rs.1,000/- per incident shall be borne by the Licensee. "
        "Major structural repairs, plumbing, electrical wiring faults, and appliance failures "
        "attributable to normal wear shall be the Licensor's responsibility.",
    ),
    (
        "Subletting Prohibition",
        "The Licensee shall not sublet, assign, or otherwise transfer possession of the "
        "licensed premises or any part thereof to any third party without prior written "
        "consent of the Licensor.",
    ),
    (
        "Use of Premises",
        "The licensed premises shall be used exclusively for residential purposes. No commercial, "
        "industrial, or illegal activity shall be carried out on the premises.",
    ),
    (
        "Utilities",
        "The Licensee shall pay electricity, water, and internet charges as per actual consumption "
        "directly to the respective service providers. Maintenance society charges (if any) shall "
        "be borne by the Licensor unless agreed otherwise in writing.",
    ),
    (
        "Pets",
        "Pets are permitted subject to: (a) no structural damage to the premises; "
        "(b) no nuisance to co-residents or neighbors; (c) compliance with society bye-laws. "
        "Any pet-related damage shall be deducted from the Security Deposit.",
    ),
    (
        "Inspection Rights",
        "The Licensor or their authorized representative may inspect the premises after giving "
        "24 hours advance notice to the Licensee.",
    ),
    (
        "Governing Law & Jurisdiction",
        "This Leave and License Agreement is governed by the Karnataka Rent Act, 1999 and the "
        "Indian Contract Act, 1872. Any disputes arising out of or in connection with this "
        "agreement shall be subject to the exclusive jurisdiction of courts in Bengaluru, "
        "Karnataka, India.",
    ),
]


# ---------------------------------------------------------------------------
# HTML generator
# ---------------------------------------------------------------------------

def generate_agreement_html(agreement) -> str:
    """
    Render a Karnataka 11-month Leave & License Agreement as HTML.

    Args:
        agreement: A `DigitalAgreement` ORM instance or any object with the
                   fields: id, property_id, tenant_id, owner_id, start_date,
                   end_date, monthly_rent, security_deposit, notice_period_days,
                   terms_json, document_hash, tenant_signed_at, owner_signed_at.

    Returns:
        Complete HTML string suitable for browser rendering or PDF conversion.
    """
    now = datetime.datetime.utcnow()

    # Parse optional custom terms stored as JSON
    custom_clauses_html = ""
    if agreement.terms_json:
        try:
            import json
            extra = json.loads(agreement.terms_json)
            if isinstance(extra, list):
                items = "".join(
                    f"<li><strong>{c.get('title','Clause')}:</strong> {c.get('text','')}</li>"
                    for c in extra
                )
                custom_clauses_html = f"""
                <div class="section">
                    <h2>Additional Agreed Clauses</h2>
                    <div class="terms-box"><ol>{items}</ol></div>
                </div>"""
        except Exception:
            pass

    # Build standard clauses substituting agreement values
    def _fmt(text: str) -> str:
        return text.format(
            monthly_rent=f"{agreement.monthly_rent:,.0f}",
            security_deposit=f"{agreement.security_deposit:,.0f}",
            notice_period_days=getattr(agreement, "notice_period_days", 60),
        )

    standard_items = "".join(
        f"<li><strong>{title}:</strong> {_fmt(body)}</li>"
        for title, body in _STANDARD_CLAUSES
    )

    # Signature rows
    def _sig_row(label: str, party_id: str, signed_at) -> str:
        date_str = (
            signed_at.strftime("%d %B %Y, %I:%M %p IST")
            if signed_at
            else "Pending Signature"
        )
        status_cls = "signed" if signed_at else "pending"
        return f"""
        <div class="sig-card {status_cls}">
            <p class="sig-role">{label}</p>
            <div class="sig-line"></div>
            <p class="sig-name">{party_id}</p>
            <p class="sig-date">{date_str}</p>
        </div>"""

    tenant_sig = _sig_row("Licensee (Tenant)", agreement.tenant_id, agreement.tenant_signed_at)
    owner_sig = _sig_row("Licensor (Owner)", agreement.owner_id, agreement.owner_signed_at)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Leave &amp; License Agreement — Rentora | AGR-{agreement.id:04d}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    @page {{ size: A4; margin: 1.8cm 1.5cm; }}
    body {{
      font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
      font-size: 12.5px; line-height: 1.65; color: #1a1a2e; background: #fff;
    }}

    /* ── Header ─────────────────────────────────────── */
    .header {{
      background: linear-gradient(135deg, #0A3D62 0%, #1565C0 100%);
      color: #fff; padding: 28px 32px 22px; border-radius: 10px 10px 0 0;
      display: flex; justify-content: space-between; align-items: flex-start;
    }}
    .header-left h1 {{ font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }}
    .header-left p {{ font-size: 11px; opacity: 0.75; margin-top: 4px; }}
    .header-right {{ text-align: right; }}
    .badge {{
      display: inline-block; background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 6px; padding: 4px 14px;
      font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
    }}
    .law-tag {{
      margin-top: 6px; font-size: 10px; opacity: 0.7;
      font-style: italic;
    }}

    /* ── Body ────────────────────────────────────────── */
    .body {{ padding: 28px 32px; }}
    .section {{ margin-bottom: 26px; }}
    .section h2 {{
      font-size: 13px; font-weight: 700; color: #0A3D62;
      text-transform: uppercase; letter-spacing: 0.8px;
      border-bottom: 2px solid #e3eaf3; padding-bottom: 7px; margin-bottom: 14px;
    }}

    /* ── Info grid ───────────────────────────────────── */
    .info-grid {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
    }}
    .info-card {{
      background: #f5f8fc; border: 1px solid #dde6f0;
      border-radius: 8px; padding: 11px 14px;
    }}
    .info-card label {{
      display: block; font-size: 9.5px; font-weight: 600;
      color: #7a94b0; text-transform: uppercase; letter-spacing: 0.6px;
      margin-bottom: 3px;
    }}
    .info-card p {{ font-size: 13px; font-weight: 700; color: #1a1a2e; }}
    .info-card.highlight {{ border-color: #1565C0; background: #eef3fb; }}
    .info-card.highlight p {{ color: #0A3D62; }}

    /* ── Parties ─────────────────────────────────────── */
    .parties-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .party-card {{
      border: 1.5px solid #dde6f0; border-radius: 8px; padding: 16px;
    }}
    .party-card .role-tag {{
      font-size: 9.5px; font-weight: 700; color: #1565C0;
      text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;
    }}
    .party-card .party-name {{ font-size: 15px; font-weight: 800; color: #1a1a2e; }}
    .party-card .party-id {{ font-size: 11px; color: #7a94b0; margin-top: 2px; }}

    /* ── Terms ───────────────────────────────────────── */
    .terms-box {{
      background: #f9fafb; border: 1px solid #e8edf3;
      border-radius: 8px; padding: 18px 22px;
    }}
    .terms-box ol {{ padding-left: 18px; }}
    .terms-box li {{ margin-bottom: 9px; font-size: 12px; color: #2c3e50; }}
    .terms-box li strong {{ color: #0A3D62; }}
    .karnataka-notice {{
      background: #fff8e1; border-left: 4px solid #f59e0b;
      border-radius: 0 6px 6px 0; padding: 10px 14px; margin-bottom: 14px;
      font-size: 11.5px; color: #78350f;
    }}

    /* ── Signatures ──────────────────────────────────── */
    .sig-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 10px; }}
    .sig-card {{
      border: 1.5px solid #dde6f0; border-radius: 10px;
      padding: 18px 20px; text-align: center;
    }}
    .sig-card.signed {{ border-color: #22c55e; background: #f0fdf4; }}
    .sig-card.pending {{ border-color: #f59e0b; background: #fffbeb; }}
    .sig-role {{ font-size: 10px; font-weight: 700; color: #0A3D62;
                 text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 14px; }}
    .sig-line {{
      height: 48px; border-bottom: 2px solid #c8d6e5;
      margin: 0 20px 10px; position: relative;
    }}
    .sig-name {{ font-size: 13px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }}
    .sig-date {{ font-size: 10.5px; color: #7a94b0; }}
    .sig-card.signed .sig-role {{ color: #15803d; }}
    .sig-card.pending .sig-role {{ color: #b45309; }}

    /* ── Footer ──────────────────────────────────────── */
    .footer {{
      border-top: 1px solid #e8edf3; margin-top: 28px;
      padding-top: 14px; text-align: center;
    }}
    .footer p {{ font-size: 10px; color: #9aadbe; line-height: 1.7; }}
    .doc-hash {{ font-family: monospace; font-size: 10px; color: #b0bec5; }}
  </style>
</head>
<body>

  <div class="header">
    <div class="header-left">
      <h1>Leave &amp; License Agreement</h1>
      <p>Rentora — Your Rental Operating System · Bengaluru, Karnataka</p>
    </div>
    <div class="header-right">
      <div class="badge">AGR-{agreement.id:04d}</div>
      <p class="law-tag">Karnataka Rent Act, 1999 · Indian Contract Act, 1872</p>
    </div>
  </div>

  <div class="body">

    <!-- ── Agreement Metadata ──────────────────────────────────── -->
    <div class="section">
      <h2>Agreement Details</h2>
      <div class="info-grid">
        <div class="info-card">
          <label>Agreement ID</label>
          <p>AGR-{agreement.id:04d}</p>
        </div>
        <div class="info-card">
          <label>Property Reference</label>
          <p>#{agreement.property_id}</p>
        </div>
        <div class="info-card">
          <label>Agreement Type</label>
          <p>Leave &amp; License</p>
        </div>
        <div class="info-card">
          <label>Commencement Date</label>
          <p>{agreement.start_date or 'To Be Confirmed'}</p>
        </div>
        <div class="info-card">
          <label>Expiry Date</label>
          <p>{agreement.end_date or 'To Be Confirmed'}</p>
        </div>
        <div class="info-card">
          <label>Term Duration</label>
          <p>11 Months</p>
        </div>
        <div class="info-card highlight">
          <label>Monthly License Fee</label>
          <p>Rs.{agreement.monthly_rent:,.0f}/-</p>
        </div>
        <div class="info-card highlight">
          <label>Security Deposit</label>
          <p>Rs.{agreement.security_deposit:,.0f}/-</p>
        </div>
        <div class="info-card">
          <label>Notice Period</label>
          <p>{getattr(agreement, 'notice_period_days', 60)} Days</p>
        </div>
      </div>
    </div>

    <!-- ── Parties ────────────────────────────────────────────── -->
    <div class="section">
      <h2>Parties to the Agreement</h2>
      <div class="parties-grid">
        <div class="party-card">
          <p class="role-tag">Licensor (Owner / Landlord)</p>
          <p class="party-name">{agreement.owner_id}</p>
          <p class="party-id">Hereinafter referred to as "The Licensor"</p>
        </div>
        <div class="party-card">
          <p class="role-tag">Licensee (Tenant)</p>
          <p class="party-name">{agreement.tenant_id}</p>
          <p class="party-id">Hereinafter referred to as "The Licensee"</p>
        </div>
      </div>
    </div>

    <!-- ── Standard Karnataka Clauses ────────────────────────── -->
    <div class="section">
      <h2>Terms &amp; Conditions</h2>
      <div class="karnataka-notice">
        ⚖️ This agreement is an 11-month Leave &amp; License arrangement and does not
        confer tenancy rights under the Karnataka Rent Act, 1999. The Licensor retains
        full ownership rights throughout the term.
      </div>
      <div class="terms-box">
        <ol>{standard_items}</ol>
      </div>
    </div>

    {custom_clauses_html}

    <!-- ── Signatures ─────────────────────────────────────────── -->
    <div class="section">
      <h2>Execution &amp; Digital Signatures</h2>
      <div class="sig-grid">
        {tenant_sig}
        {owner_sig}
      </div>
    </div>

    <!-- ── Footer ─────────────────────────────────────────────── -->
    <div class="footer">
      <p>
        This Leave &amp; License Agreement has been digitally generated and executed on the
        Rentora platform. Both parties acknowledge having read, understood, and agreed to all
        terms stated herein. This document constitutes a legally binding agreement under the
        Indian Contract Act, 1872.
      </p>
      <p class="doc-hash">
        Document Hash: {agreement.document_hash or 'N/A'} &nbsp;|&nbsp;
        Generated: {now.strftime('%d %B %Y, %I:%M %p UTC')}
      </p>
    </div>

  </div>
</body>
</html>"""
