import json
import logging
import asyncio
from typing import Any, Dict
import uuid
from datetime import datetime

try:
    from aiokafka import AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger("kafka_producer")

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

async def emit_event(event_type: str, payload: Dict[str, Any], source: str):
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
        logger.warning(f"[KAFKA MOCK] Emitting {event_type} from {source}: {json.dumps(payload)}")
        return

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    await producer.start()
    try:
        await producer.send_and_wait(event_type, event)
        logger.info(f"Event {event_type} emitted to Kafka.")
    except Exception as e:
        logger.error(f"Failed to emit event {event_type}: {e}")
    finally:
        await producer.stop()
