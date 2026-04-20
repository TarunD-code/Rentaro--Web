import logging

logger = logging.getLogger("billing_service")

class KafkaProducer:
    def __init__(self):
        logger.info("Mock Kafka Producer initialized (Billing).")
    
    async def produce(self, topic: str, value: dict):
        logger.debug(f"Mock Produce to {topic}: {value}")

    async def start(self):
        pass

    async def stop(self):
        pass
