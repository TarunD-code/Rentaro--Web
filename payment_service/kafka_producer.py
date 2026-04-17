import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

try:
    from aiokafka import AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger("payment_service.kafka")

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

async def emit_event(event_type: str, payload: Dict[str, Any], source: str = "payment-service"):
    """
    Emit a domain event to Kafka.
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "payload": payload
    }

    if not KAFKA_AVAILABLE:
        logger.warning(f"[KAFKA MOCK] Emitting {event_type}: {json.dumps(payload)}")
        return

    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        await producer.send_and_wait(event_type, event)
        logger.info(f"Event {event_type} emitted to Kafka topic {event_type}")
        await producer.stop()
    except Exception as e:
        logger.error(f"Failed to emit Kafka event: {e}")
