import logging
logger = logging.getLogger("notification_service.dispatchers.email")

async def send_email(email: str, subject: str, template_name: str, context: dict):
    """
    Send email via SMTP/SendGrid.
    In production, use jinja2 for rendering and sendgrid-python.
    """
    logger.info(f"[EMAIL MOCK] Sending to {email}: {subject} using template {template_name}")
    # Integration code for SMTP/SendGrid goes here
    return True
