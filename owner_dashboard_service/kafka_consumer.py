import asyncio
import logging

logger = logging.getLogger("owner_dashboard")

async def start_metrics_consumer():
    """
    Mock Kafka consumer that simulates background metrics ingestion.
    In a real production environment, this would connect to a Kafka broker.
    """
    logger.info("Mock Kafka Consumer initialized. Waiting for events...")
    while True:
        # Simulate processing delay
        await asyncio.sleep(60)
        logger.debug("Mock Consumer heartbeat: active")
