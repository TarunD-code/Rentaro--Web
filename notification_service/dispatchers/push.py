import logging
logger = logging.getLogger("notification_service.dispatchers.push")

async def send_push(token: str, title: str, body: str, data: dict = None):
    """
    Send push notification via FCM.
    In production, use firebase_admin.messaging.
    """
    logger.info(f"[PUSH MOCK] Sending to token {token[:10]}...: {title} - {body}")
    # Integration code for FCM goes here
    return True
