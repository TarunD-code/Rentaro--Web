import logging
import httpx
import shared_event_broker

logger = logging.getLogger("billing_service")

class KafkaProducer:
    @classmethod
    async def produce(cls, topic: str, value: dict):
        logger.info(f"Dispatching event to topic {topic}: {value}")
        
        # 1. Publish asynchronous event via central RabbitMQ message broker
        try:
            shared_event_broker.publish_event(
                routing_key=topic,
                payload=value,
                source_service="billing_service"
            )
        except Exception as ex:
            logger.error(f"Failed to publish event via RabbitMQ: {ex}")
            
        # 2. Resilient synchronous HTTP dispatch callback fallback for local/legacy compatibility
        async with httpx.AsyncClient() as client:
            try:
                # Dispatch to Property Service
                await client.post("http://127.0.0.1:8003/internal/events", json={"topic": topic, "value": value}, timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to dispatch HTTP to Property Service: {e}")
                
            try:
                # Dispatch to Notification Service
                await client.post("http://127.0.0.1:8013/internal/events", json={"topic": topic, "value": value}, timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to dispatch HTTP to Notification Service: {e}")

    async def start(self):
        pass

    async def stop(self):
        pass

