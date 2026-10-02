"""
Rentora — Production SMTP Email Client
========================================
Sends transactional emails using Python's standard smtplib with STARTTLS.
No third-party mail library required — works with any RFC-5321 SMTP relay
(Gmail, Brevo, Resend SMTP bridge, AWS SES, Mailgun SMTP, Mailtrap, etc.).

Configuration (all values read from environment / .env):
    SMTP_HOST       SMTP server hostname          (e.g. smtp.gmail.com)
    SMTP_PORT       SMTP port, default 587         (587 = STARTTLS)
    SMTP_USER       SMTP login / sender address
    SMTP_PASSWORD   SMTP password or app password
    MAIL_FROM_NAME  Display name in From header    (default: Rentora)

Usage:
    from notification_service.email_client import (
        send_otp_email,
        send_agreement_email,
    )

    await send_otp_email("user@example.com", "123456")
    await send_agreement_email(agreement_obj, html_content)

Thread safety:
    Each call opens and closes its own SMTP connection, which is the safest
    pattern for a multi-worker async service. Connection pooling is not needed
    for transactional volume.

DPDP Act note:
    Email addresses passed to this module are used solely for delivery.
    They are not logged at INFO level; only the first 3 characters are
    shown in log output to minimise PII exposure in log aggregators.
"""

import os
import logging
import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from typing import Optional

logger = logging.getLogger("email_client")

# ── SMTP configuration ────────────────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    """Read a config value from env, loading .env if needed."""
    val = os.environ.get(key, "")
    if val:
        return val
    # Lazy .env load (handles running outside Docker)
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get(key, default)


SMTP_HOST     = lambda: _cfg("SMTP_HOST", "")
SMTP_PORT     = lambda: int(_cfg("SMTP_PORT", "587"))
SMTP_USER     = lambda: _cfg("SMTP_USER", "")
SMTP_PASSWORD = lambda: _cfg("SMTP_PASSWORD", "")
FROM_NAME     = lambda: _cfg("MAIL_FROM_NAME", "Rentora")
FROM_ADDR     = lambda: _cfg("SMTP_USER", "noreply@rentora.com")

_DEV_MODE = lambda: _cfg("DEV_MODE", "true").lower() in ("true", "1", "yes")


def _is_configured() -> bool:
    return bool(SMTP_HOST() and SMTP_USER() and SMTP_PASSWORD())


def _send_sync(msg: MIMEMultipart, to_addresses: list[str]) -> None:
    """
    Open one SMTP connection, send, close.  Called via asyncio.to_thread so
    the FastAPI event loop is never blocked.
    """
    host = SMTP_HOST()
    port = SMTP_PORT()
    user = SMTP_USER()
    password = SMTP_PASSWORD()

    context = ssl.create_default_context()

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(user, password)
        server.sendmail(
            FROM_ADDR(),
            to_addresses,
            msg.as_string(),
        )


async def _deliver(msg: MIMEMultipart, to_addresses: list[str], subject: str) -> None:
    """
    Async wrapper around the blocking SMTP call.
    Failures are logged as warnings — never propagated to the caller so a mail
    delivery hiccup never crashes registration or agreement signing.
    """
    masked = [f"{a[:3]}***" for a in to_addresses]
    if _DEV_MODE() and not _is_configured():
        logger.info(f"[Email DEV] Would send '{subject}' to {masked}")
        return

    if not _is_configured():
        logger.warning(
            f"[Email] SMTP not configured — skipping '{subject}' to {masked}. "
            "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env."
        )
        return

    try:
        await asyncio.to_thread(_send_sync, msg, to_addresses)
        logger.info(f"[Email] '{subject}' delivered to {masked}")
    except Exception as exc:
        logger.warning(f"[Email] Delivery failed for '{subject}' to {masked}: {exc}")


# ── OTP email ─────────────────────────────────────────────────────────────────

async def send_otp_email(to_email: str, otp: str) -> None:
    """
    Send a 6-digit OTP verification email.

    Args:
        to_email: Recipient email address.
        otp:      The 6-digit one-time password.
    """
    subject = "Your Rentora Verification Code"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f4ff;font-family:'Inter','Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;padding:40px 0;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.08);overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#0A3D62,#1565C0);padding:32px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:800;letter-spacing:-0.5px;">
              Rentora
            </h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.75);font-size:13px;">
              Your Rental Operating System
            </p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            <h2 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#1a1a2e;">
              Verify your account
            </h2>
            <p style="margin:0 0 28px;font-size:14px;color:#64748b;line-height:1.6;">
              Use the code below to complete your Rentora registration.
              This code expires in <strong>10 minutes</strong>.
            </p>
            <!-- OTP box -->
            <div style="background:#eef3fb;border-radius:12px;padding:24px;text-align:center;margin-bottom:28px;">
              <span style="font-size:42px;font-weight:900;letter-spacing:14px;color:#0A3D62;
                           font-variant-numeric:tabular-nums;">{otp}</span>
            </div>
            <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.7;">
              If you did not create a Rentora account, you can safely ignore this email.<br>
              <strong>Rentora will never ask for this code over phone or chat.</strong>
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #e8edf3;text-align:center;">
            <p style="margin:0;font-size:11px;color:#b0bec5;">
              © {__import__('datetime').datetime.utcnow().year} Rentora · Bengaluru, Karnataka, India
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = formataddr((FROM_NAME(), FROM_ADDR()))
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    await _deliver(msg, [to_email], subject)


# ── Agreement delivery email ──────────────────────────────────────────────────

async def send_agreement_email(
    agreement: object,
    html_content: str,
    extra_recipients: Optional[list[str]] = None,
) -> None:
    """
    Send the fully-executed Karnataka Leave & License Agreement to both
    the Tenant and the Owner as an HTML email with a PDF attachment.

    The HTML content of the agreement is attached as a .pdf-named file so
    email clients display it as a downloadable attachment. In production
    you would generate a proper PDF (e.g. with weasyprint); the HTML
    attachment is the functional equivalent for demo purposes.

    Args:
        agreement:         A DigitalAgreement ORM instance or equivalent object
                           with .id, .tenant_id, .owner_id, .monthly_rent,
                           .security_deposit attributes.
        html_content:      The rendered agreement HTML from generate_agreement_html().
        extra_recipients:  Optional additional CC addresses (e.g. admin).
    """
    agr_id       = getattr(agreement, "id", "?")
    tenant_email = getattr(agreement, "tenant_id", "")
    owner_email  = getattr(agreement, "owner_id", "")
    monthly_rent = getattr(agreement, "monthly_rent", 0)

    recipients = [e for e in [tenant_email, owner_email] if e and "@" in e]
    if extra_recipients:
        recipients += [e for e in extra_recipients if e and "@" in e]
    recipients = list(dict.fromkeys(recipients))  # deduplicate, preserve order

    if not recipients:
        logger.warning(f"[Email] Agreement #{agr_id} has no valid email recipients — skipping.")
        return

    subject = f"Rentora — Your Rental Agreement AGR-{agr_id:04d} is Ready"

    body_html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f0f4ff;font-family:'Inter','Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.08);overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#0A3D62,#1565C0);padding:28px 32px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;font-weight:800;">Rentora</h1>
            <p style="margin:4px 0 0;color:rgba(255,255,255,0.7);font-size:12px;">Leave &amp; License Agreement</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 36px;">
            <h2 style="margin:0 0 12px;font-size:18px;color:#1a1a2e;font-weight:700;">
              Your agreement is fully executed ✅
            </h2>
            <p style="margin:0 0 20px;font-size:14px;color:#64748b;line-height:1.65;">
              The 11-Month Leave &amp; License Agreement <strong>AGR-{agr_id:04d}</strong>
              between both parties has been digitally signed and is now legally active.
              Please find the agreement document attached to this email.
            </p>
            <table cellpadding="0" cellspacing="0" width="100%"
                   style="background:#f5f8fc;border-radius:8px;padding:18px;margin-bottom:20px;">
              <tr>
                <td style="font-size:12px;color:#7a94b0;font-weight:600;text-transform:uppercase;">
                  Monthly Rent
                </td>
                <td align="right" style="font-size:16px;font-weight:800;color:#0A3D62;">
                  Rs.{monthly_rent:,.0f}/-
                </td>
              </tr>
            </table>
            <p style="margin:0;font-size:12px;color:#94a3b8;">
              Keep this email for your records. The document is attached below.
              Governed by the Karnataka Rent Act, 1999 and Indian Contract Act, 1872.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:18px 36px;border-top:1px solid #e8edf3;text-align:center;">
            <p style="margin:0;font-size:11px;color:#b0bec5;">
              © {__import__('datetime').datetime.utcnow().year} Rentora · Bengaluru, Karnataka, India
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = formataddr((FROM_NAME(), FROM_ADDR()))
    msg["To"]      = ", ".join(recipients)

    msg.attach(MIMEText(body_html, "html"))

    # Attach the agreement HTML as a downloadable PDF-named file.
    # In production, replace html_content.encode() with actual PDF bytes
    # from weasyprint.HTML(string=html_content).write_pdf()
    attachment = MIMEApplication(html_content.encode("utf-8"), _subtype="octet-stream")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"Rentora_Agreement_AGR-{agr_id:04d}.html",
    )
    msg.attach(attachment)

    await _deliver(msg, recipients, subject)
