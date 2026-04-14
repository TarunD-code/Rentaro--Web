"""
Payment Service — Notification Templates & Dispatcher

In sandbox mode, logs all notifications to console.
In production, integrates with SendGrid (email) and Twilio (SMS).
"""

import os
import logging
import datetime
from typing import Optional

logger = logging.getLogger("payment_service.notifications")

IS_SANDBOX = not bool(os.environ.get("SENDGRID_API_KEY"))


def send_rent_reminder(
    tenant_email: str,
    tenant_phone: Optional[str],
    tenant_name: str,
    amount: float,
    due_date: datetime.datetime,
    property_title: str,
):
    """Send rent reminder via email and SMS."""
    subject = f"Rent Reminder: ₹{amount:,.0f} due on {due_date.strftime('%B %d, %Y')}"
    body = f"""
    Hi {tenant_name},

    This is a friendly reminder that your rent of ₹{amount:,.0f} for "{property_title}" 
    is due on {due_date.strftime('%B %d, %Y')}.

    You can pay instantly through Rentora:
    → Login → Dashboard → Pay Now

    If you've already set up auto-pay, no action is needed!

    Best regards,
    Team Rentora
    """

    if IS_SANDBOX:
        logger.info(f"[SANDBOX EMAIL] To: {tenant_email} | Subject: {subject}")
        logger.info(f"[SANDBOX EMAIL] Body: {body.strip()}")
        if tenant_phone:
            sms = f"Rentora: Your rent of ₹{amount:,.0f} is due on {due_date.strftime('%d %b')}. Pay now at rentora.com"
            logger.info(f"[SANDBOX SMS] To: {tenant_phone} | Message: {sms}")
        return True

    # Production: SendGrid + Twilio
    _send_email(tenant_email, subject, body)
    if tenant_phone:
        _send_sms(tenant_phone, f"Rentora: Rent ₹{amount:,.0f} due {due_date.strftime('%d %b')}. Pay at rentora.com")
    return True


def send_payment_receipt(
    tenant_email: str,
    tenant_name: str,
    transaction_id: int,
    amount: float,
    payment_method: str,
    paid_at: datetime.datetime,
    property_title: str,
):
    """Send payment receipt after successful transaction."""
    subject = f"Payment Receipt — ₹{amount:,.0f} for {property_title}"
    body = f"""
    Hi {tenant_name},

    Your payment has been received successfully!

    Transaction ID: TXN-{transaction_id:06d}
    Amount: ₹{amount:,.0f}
    Method: {payment_method.upper()}
    Date: {paid_at.strftime('%B %d, %Y at %I:%M %p')}
    Property: {property_title}

    Thank you for being a Rentora member.

    Best regards,
    Team Rentora
    """

    if IS_SANDBOX:
        logger.info(f"[SANDBOX EMAIL] Receipt to: {tenant_email} | Subject: {subject}")
        logger.info(f"[SANDBOX EMAIL] Body: {body.strip()}")
        return True

    _send_email(tenant_email, subject, body)
    return True


def send_autopay_failure(
    tenant_email: str,
    tenant_name: str,
    amount: float,
    reason: str,
    property_title: str,
):
    """Notify tenant about failed auto-pay charge."""
    subject = f"Auto-Pay Failed — Action Required for {property_title}"
    body = f"""
    Hi {tenant_name},

    Your auto-pay charge of ₹{amount:,.0f} for "{property_title}" has failed.

    Reason: {reason}

    Please pay manually through Rentora to avoid late fees:
    → Login → Dashboard → Pay Now

    If this continues, please update your payment method.

    Best regards,
    Team Rentora
    """

    if IS_SANDBOX:
        logger.info(f"[SANDBOX EMAIL] Auto-pay failure to: {tenant_email}")
        logger.info(f"[SANDBOX EMAIL] Body: {body.strip()}")
        return True

    _send_email(tenant_email, subject, body)
    return True


def send_mandate_activated(tenant_email: str, tenant_name: str, property_title: str):
    """Notify tenant that auto-pay mandate is now active."""
    subject = f"Auto-Pay Activated for {property_title}"
    body = f"""
    Hi {tenant_name},

    Great news! Your auto-pay has been activated for "{property_title}".

    Your rent will be automatically deducted on the 1st of each month.
    You can manage or cancel auto-pay anytime from your Rentora dashboard.

    Best regards,
    Team Rentora
    """

    if IS_SANDBOX:
        logger.info(f"[SANDBOX EMAIL] Mandate activated to: {tenant_email}")
        return True

    _send_email(tenant_email, subject, body)
    return True


# ── Production Integrations (stubs) ─────────────────────────────────────────

def _send_email(to: str, subject: str, body: str):
    """Send email via SendGrid. Requires SENDGRID_API_KEY env var."""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        message = Mail(
            from_email="payments@rentora.com",
            to_emails=to,
            subject=subject,
            plain_text_content=body,
        )
        sg.send(message)
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")


def _send_sms(to: str, message: str):
    """Send SMS via Twilio. Requires TWILIO_SID and TWILIO_AUTH_TOKEN env vars."""
    try:
        from twilio.rest import Client

        client = Client(
            os.environ.get("TWILIO_SID"),
            os.environ.get("TWILIO_AUTH_TOKEN"),
        )
        client.messages.create(
            body=message,
            from_=os.environ.get("TWILIO_PHONE", "+1234567890"),
            to=to,
        )
        logger.info(f"SMS sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to}: {e}")
