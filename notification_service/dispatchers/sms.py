import logging
logger = logging.getLogger("notification_service.dispatchers.sms")

async def send_sms(phone: str, message: str):
    """
    Send SMS via Twilio.
    In production, use twilio.rest.
    """
    logger.info(f"[SMS MOCK] Sending to {phone}: {message}")
    # Integration code for Twilio goes here
    return True
