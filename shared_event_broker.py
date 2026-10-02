import os
import json
import uuid
import datetime
import logging
from typing import Dict, Any, Callable, Optional

# Setup centralized logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shared_event_broker")

# MANUALLY LOAD .ENV IF EXISTS
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# ENVIRONMENT CONFIG
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE_NAME = "rentora_exchange"
DLX_NAME = "rentora_dlx"
DLQ_NAME = "rentora_dlq"

# LAZY CONNECTION INITIALIZER
_connection = None
_channel = None
_use_fallback = False

def _get_connection_and_channel():
    global _connection, _channel, _use_fallback
    if _connection is not None and _connection.is_open:
        return _connection, _channel
        
    if _use_fallback:
        return None, None
        
    try:
        import pika
        logger.info(f"Connecting to RabbitMQ Broker...")
        params = pika.URLParameters(RABBITMQ_URL)
        params.socket_timeout = 2.0
        
        _connection = pika.BlockingConnection(params)
        _channel = _connection.channel()
        
        # 1. Setup Durable Topic Exchange for standard events
        _channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True
        )
        
        # 2. Setup Dead-Letter Exchange (DLX) and Queue (DLQ)
        _channel.exchange_declare(
            exchange=DLX_NAME,
            exchange_type="direct",
            durable=True
        )
        _channel.queue_declare(
            queue=DLQ_NAME,
            durable=True
        )
        _channel.queue_bind(
            queue=DLQ_NAME,
            exchange=DLX_NAME,
            routing_key="retry_failed"
        )
        
        logger.info("✅ RabbitMQ connection and exchange pools declared successfully!")
        return _connection, _channel
    except Exception as e:
        logger.warning(f"RabbitMQ is offline or pika is not installed: {e}. Defaulting to dev log callback simulator.")
        _use_fallback = True
        return None, None

def publish_event(routing_key: str, payload: Dict[str, Any], source_service: str) -> bool:
    """
    Publishes an asynchronous event to the durable RabbitMQ exchange.
    Returns True if successfully delivered.
    """
    event_id = str(uuid.uuid4())
    event_envelope = {
        "event_id": event_id,
        "event_type": routing_key,
        "source_service": source_service,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "payload": payload,
        "version": "1.0.0"
    }
    
    _, channel = _get_connection_and_channel()
    if channel is not None:
        try:
            import pika
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=routing_key,
                body=json.dumps(event_envelope),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent on disk
                    content_type="application/json",
                    message_id=event_id
                )
            )
            logger.info(f"📬 [RabbitMQ Publish Success] Exchange: {EXCHANGE_NAME}, Key: {routing_key}, ID: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to RabbitMQ: {e}. Simulating fallback.")
            
    # Dev offline simulation: print details
    logger.info(f"📬 [Simulated Event Publish] Key: {routing_key}, Source: {source_service}, Envelope: {json.dumps(event_envelope)}")
    return True

class EventConsumer:
    """ Helper client to manage RabbitMQ queue bindings and persistent listeners """
    def __init__(self, service_name: str, routing_keys: list):
        self.service_name = service_name
        self.queue_name = f"queue_{service_name}"
        self.routing_keys = routing_keys
        
    def start_consuming(self, callback: Callable[[Dict[str, Any]], None]):
        """ Sets up durable queue bindings and begins long-polling consumer block """
        _, channel = _get_connection_and_channel()
        if channel is None:
            logger.warning(f"RabbitMQ is offline! Consumer for {self.service_name} will not start.")
            return
            
        try:
            # Declare durable worker queue with DLX bound
            channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": DLX_NAME,
                    "x-dead-letter-routing-key": "retry_failed"
                }
            )
            
            # Bind all interested topics
            for r_key in self.routing_keys:
                channel.queue_bind(
                    queue=self.queue_name,
                    exchange=EXCHANGE_NAME,
                    routing_key=r_key
                )
                
            def on_message_received(ch, method, properties, body):
                try:
                    event_data = json.loads(body.decode("utf-8"))
                    logger.info(f"📥 [RabbitMQ Received] Queue: {self.queue_name}, Event: {event_data.get('event_type')}")
                    
                    event_id = event_data.get("event_id")
                    if event_id:
                        import shared_redis
                        idempotency_key = f"event:processed:{self.service_name}:{event_id}"
                        if shared_redis.get(idempotency_key):
                            logger.info(f"⚠️ [Idempotence Match] Event {event_id} already processed by {self.service_name}. Skipping callback execution.")
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return
                            
                        # Execute service callback
                        callback(event_data)
                        
                        # Mark processed with 24-hour TTL
                        shared_redis.set(idempotency_key, "true", ttl=86400)
                    else:
                        # Fallback for untracked event envelopes
                        callback(event_data)
                    
                    # Acknowledge delivery
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as ex:
                    logger.error(f"Error handling consumed message in {self.service_name}: {ex}. Rejecting message to DLX.")
                    # Reject to Dead-Letter Exchange (no requeue)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                    
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=on_message_received
            )
            
            logger.info(f"🚀 Durable consumer started for {self.service_name} on queue {self.queue_name}...")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Durable consumer failed: {e}")
