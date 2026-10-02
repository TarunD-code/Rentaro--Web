import json
import logging
import threading
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
import shared_event_broker
import shared_redis

logger = logging.getLogger("property_service.event_broker")

def process_featured_event(event_data: dict):
    """Callback function to process featured listing purchases."""
    try:
        # standard structure check
        payload = event_data.get("payload", {})
        property_id = payload.get("property_id")
        
        if property_id:
            db = SessionLocal()
            prop = db.query(models.Property).filter(models.Property.id == property_id).first()
            if prop:
                prop.is_featured = True
                db.commit()
                logger.info(f"Property {property_id} is now FEATURED via Event Broker.")
                
                # Active Cache Invalidation on Event Receipt
                try:
                    shared_redis.delete(shared_redis.get_property_key(property_id))
                    shared_redis.invalidate_search_cache()
                except Exception as ex:
                    logger.warning(f"Failed to clear cache on RabbitMQ event: {ex}")
            db.close()
    except Exception as e:
        logger.error(f"Error processing RabbitMQ event inside callback: {e}")

async def start_featured_entitlement_consumer():
    """Start EventConsumer on a separate daemon thread to avoid blocking."""
    logger.info("Initializing Property Service RabbitMQ Event Consumer...")
    
    def consumer_thread_target():
        try:
            consumer = shared_event_broker.EventConsumer(
                service_name="property_service",
                routing_keys=["featured-listing-purchases"]
            )
            consumer.start_consuming(process_featured_event)
        except Exception as e:
            logger.error(f"RabbitMQ consumer thread crashed: {e}")
            
    t = threading.Thread(target=consumer_thread_target, daemon=True)
    t.start()
    logger.info("Property Service Event Consumer Thread successfully spawned.")

