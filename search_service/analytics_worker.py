"""
Analytics Worker — Priority 4 Rentora Search Intelligence
RabbitMQ consumer that batches analytics events and persists them to PostgreSQL.
Run as a standalone process: python -m search_service.analytics_worker
"""
import os
import sys
import json
import time
import logging
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics_worker")

# Batch settings
BATCH_SIZE = 50
FLUSH_INTERVAL_SEC = 5.0

_event_buffer: List[Dict[str, Any]] = []
_last_flush = time.time()


def _flush_batch(buffer: List[Dict[str, Any]]) -> bool:
    """Batch-insert analytics events into search.analytics_events."""
    if not buffer:
        return True

    try:
        import shared_database
        from sqlalchemy import text

        with shared_database.sync_engine.connect() as conn:
            for evt in buffer:
                conn.execute(text("""
                    INSERT INTO search.analytics_events
                    (event_type, user_id, session_id, property_id, search_query,
                     filters_json, result_count, position_clicked, dwell_seconds,
                     ip_hash, created_at)
                    VALUES (:event_type, :user_id, :session_id, :property_id, :search_query,
                            :filters_json, :result_count, :position_clicked, :dwell_seconds,
                            :ip_hash, NOW())
                """), {
                    "event_type": evt.get("event_type"),
                    "user_id": evt.get("user_id"),
                    "session_id": evt.get("session_id"),
                    "property_id": evt.get("property_id"),
                    "search_query": evt.get("search_query"),
                    "filters_json": evt.get("filters_json"),
                    "result_count": evt.get("result_count"),
                    "position_clicked": evt.get("position_clicked"),
                    "dwell_seconds": evt.get("dwell_seconds"),
                    "ip_hash": evt.get("ip_hash"),
                })
            conn.commit()

        # Also save search queries to history table
        for evt in buffer:
            if evt.get("event_type") == "analytics.search_performed" and evt.get("user_id"):
                try:
                    with shared_database.sync_engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO search.search_history
                            (user_id, query, filters_json, result_count, searched_at)
                            VALUES (:uid, :query, :filters, :count, NOW())
                        """), {
                            "uid": evt["user_id"],
                            "query": evt.get("search_query", ""),
                            "filters": evt.get("filters_json"),
                            "count": evt.get("result_count", 0),
                        })
                        conn.commit()
                except Exception:
                    pass

        logger.info(f"[Analytics Worker] Flushed {len(buffer)} events to DB")
        return True
    except Exception as e:
        logger.error(f"[Analytics Worker] Flush failed: {e}")
        return False


def _on_event(channel, method, properties, body):
    """RabbitMQ message callback for analytics events."""
    global _event_buffer, _last_flush

    try:
        evt = json.loads(body)
        _event_buffer.append(evt)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Failed to decode analytics event: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    # Flush on batch size or time interval
    now = time.time()
    if len(_event_buffer) >= BATCH_SIZE or (now - _last_flush) >= FLUSH_INTERVAL_SEC:
        batch = _event_buffer[:]
        _event_buffer = []
        _last_flush = now
        _flush_batch(batch)


def run_worker():
    """Start the analytics RabbitMQ consumer worker."""
    logger.info("[Analytics Worker] Starting...")

    try:
        import pika
        RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        params = pika.URLParameters(RABBITMQ_URL)
        params.socket_timeout = 5.0

        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declare analytics queue bound to rentora_exchange
        channel.queue_declare(
            queue="search_analytics_queue",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "rentora_dlx",
                "x-dead-letter-routing-key": "dlq.search_analytics",
            }
        )
        channel.queue_bind(
            queue="search_analytics_queue",
            exchange="rentora_exchange",
            routing_key="analytics.#",
        )

        channel.basic_qos(prefetch_count=100)
        channel.basic_consume(queue="search_analytics_queue", on_message_callback=_on_event)

        logger.info("[Analytics Worker] Ready. Consuming analytics.# events...")
        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info("[Analytics Worker] Shutting down...")
    except Exception as e:
        logger.error(f"[Analytics Worker] Failed to start: {e}")
        # Flush remaining buffer on crash
        if _event_buffer:
            _flush_batch(_event_buffer)


if __name__ == "__main__":
    run_worker()
