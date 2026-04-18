import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

logger = logging.getLogger("property_service.kafka")

async def start_featured_entitlement_consumer():
    """Consume 'featured.purchase.completed' events to mark properties as featured."""
    consumer = AIOKafkaConsumer(
        "featured-listing-purchases",
        bootstrap_servers="localhost:9092",
        group_id="property_service_featured_group",
        auto_offset_reset="earliest"
    )
    
    await consumer.start()
    logger.info("Property Service Kafka Consumer for Featured Listings started.")
    
    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode("utf-8"))
                event_type = data.get("event_type")
                
                if event_type == "featured.purchase.completed":
                    payload = data.get("payload", {})
                    property_id = payload.get("property_id")
                    
                    if property_id:
                        db = SessionLocal()
                        prop = db.query(models.Property).filter(models.Property.id == property_id).first()
                        if prop:
                            prop.is_featured = True
                            db.commit()
                            logger.info(f"Property {property_id} is now FEATURED.")
                        db.close()
            except Exception as e:
                logger.error(f"Error processing featured listing event: {e}")
    finally:
        await consumer.stop()
