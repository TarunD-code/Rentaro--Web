import json
import logging
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

# For production, use aiokafka. For local/mock, we use a simple queue.
try:
    from aiokafka import AIOKafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from . import models, database

logger = logging.getLogger("notification_service.consumer")

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = ["rent.due", "visit.reminder", "message.received", "user.signup"]

async def process_event(event_data: dict):
    """Business logic to map events to actual notifications."""
    db: Session = next(database.get_db())
    
    event_id = event_data.get("event_id")
    event_type = event_data.get("event_type")
    payload = event_data.get("payload", {})
    
    # Idempotency check
    existing = db.query(models.Notification).filter(models.Notification.event_id == event_id).first()
    if existing:
        logger.info(f"Duplicate event ignored: {event_id}")
        return

    # Routing logic
    recipient_id = None
    content = ""
    
    if event_type == "rent.due":
        recipient_id = str(payload.get("tenant_id"))
        content = f"Reminder: Your rent of ₹{payload.get('amount')} is due on {payload.get('due_date')}."
    elif event_type == "message.received":
        recipient_id = str(payload.get("receiver_id"))
        content = f"New message regarding property {payload.get('property_id')}: {payload.get('body')[:50]}..."
    elif event_type == "user.signup":
        recipient_id = str(payload.get("user_id"))
        content = "Welcome to Rentora! We're glad to have you on board."
    
    if not recipient_id:
        logger.warning(f"No recipient found for event {event_type}")
        return

    # Check preferences
    prefs = db.query(models.NotificationPreference).filter(
        models.NotificationPreference.user_id == recipient_id
    ).first()
    
    # For Sprint 17, we always create the 'in-app' record
    notif = models.Notification(
        event_id=event_id,
        user_id=recipient_id,
        type=event_type,
        content=content,
        payload=payload,
        channel="all", # Default to record only first
        status="pending"
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    logger.info(f"Created notification {notif.id} for user {recipient_id}")

    # Trigger Dispatchers (Push, Email, SMS)
    # TODO: In real implementation, these would be separate async tasks
    await dispatch_notification(notif, prefs)

async def dispatch_notification(notif, prefs):
    """Placeholder for external dispatching (FCM, Email, SMS)."""
    # Logic to check prefs.push_enabled, prefs.email_enabled etc.
    logger.info(f"Dispatching notification {notif.id} via configured channels.")
    # Implementation follows in dispatchers/
    notif.status = "sent"
    notif.sent_at = datetime.utcnow()
    # db.commit() # would be needed if we had a live session here

async def run_kafka_consumer():
    if not KAFKA_AVAILABLE:
        logger.warning("aiokafka not installed. Running in Mock Event mode (looping mocks).")
        while True:
            # Simulate an event every 60 seconds for demo
            await asyncio.sleep(60)
            mock_event = {
                "event_id": f"mock-{datetime.now().timestamp()}",
                "event_type": "user.signup",
                "payload": {"user_id": "test_user_ignited"}
            }
            await process_event(mock_event)
        return

    consumer = AIOKafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    await consumer.start()
    try:
        async for msg in consumer:
            logger.info(f"Consumed message: {msg.value}")
            await process_event(msg.value)
    finally:
        await consumer.stop()
