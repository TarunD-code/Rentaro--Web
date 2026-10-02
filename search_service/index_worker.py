"""
Property Index Worker — Priority 4 Rentora Search Intelligence
RabbitMQ consumer that keeps search.property_index in sync with property changes.
Run as: python -m search_service.index_worker
"""
import os
import sys
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("index_worker")

ROUTING_KEYS = [
    "property.created",
    "property.updated",
    "property.deleted",
    "property.media_updated",
    "locality_score_updated",
]


def _upsert_property(payload: dict) -> bool:
    """Upsert a denormalized property document into search.property_index."""
    pid = payload.get("property_id") or payload.get("id")
    if not pid:
        return False

    # Deduplicate via Redis lock
    try:
        import shared_redis
        lock_key = f"index_lock:{pid}"
        if not shared_redis.acquire_lock(lock_key, expire_seconds=10):
            logger.warning(f"[Index Worker] Skipping duplicate event for property {pid}")
            return False
    except Exception:
        pass

    try:
        import shared_database
        from sqlalchemy import text

        with shared_database.sync_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO search.property_index (
                    property_id, title, description, address, city, state,
                    property_type, price, lat, lng, amenities, is_featured, is_verified,
                    is_furnished, is_pet_friendly, owner_verified, locality_score,
                    commute_score, metro_score, hospital_score, school_score,
                    walkability_score, media_count, status, tags, 
                    images, locality, bedrooms, bathrooms, furnishing, indexed_at, updated_at
                ) VALUES (
                    :pid, :title, :desc, :addr, :city, :state,
                    :ptype, :price, :lat, :lng, :amenities, :featured, :verified,
                    :furnished, :pet, :owner_verified, :ls, :cs, :ms, :hs, :ss, :ws,
                    :media, :status, :tags, 
                    :images, :locality, :bedrooms, :bathrooms, :furnishing, NOW(), NOW()
                )
                ON CONFLICT (property_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    property_type = EXCLUDED.property_type,
                    price = EXCLUDED.price,
                    lat = EXCLUDED.lat,
                    lng = EXCLUDED.lng,
                    amenities = EXCLUDED.amenities,
                    is_featured = EXCLUDED.is_featured,
                    is_verified = EXCLUDED.is_verified,
                    is_furnished = EXCLUDED.is_furnished,
                    is_pet_friendly = EXCLUDED.is_pet_friendly,
                    locality_score = COALESCE(EXCLUDED.locality_score, search.property_index.locality_score),
                    commute_score = COALESCE(EXCLUDED.commute_score, search.property_index.commute_score),
                    media_count = EXCLUDED.media_count,
                    status = EXCLUDED.status,
                    tags = EXCLUDED.tags,
                    images = EXCLUDED.images,
                    locality = EXCLUDED.locality,
                    bedrooms = EXCLUDED.bedrooms,
                    bathrooms = EXCLUDED.bathrooms,
                    furnishing = EXCLUDED.furnishing,
                    updated_at = NOW()
            """), {
                "pid": pid,
                "title": payload.get("title", ""),
                "desc": payload.get("description", ""),
                "addr": payload.get("address", ""),
                "city": payload.get("city", ""),
                "state": payload.get("state", ""),
                "ptype": payload.get("property_type", ""),
                "price": payload.get("price", 0),
                "lat": payload.get("lat"),
                "lng": payload.get("lng"),
                "amenities": ",".join(payload.get("amenities", [])) if isinstance(payload.get("amenities"), list) else payload.get("amenities", ""),
                "featured": payload.get("is_featured", False),
                "verified": payload.get("is_verified", False),
                "furnished": payload.get("is_furnished", False),
                "pet": payload.get("is_pet_friendly", False),
                "owner_verified": payload.get("owner_verified", False),
                "ls": payload.get("locality_score", 0),
                "cs": payload.get("commute_score", 0),
                "ms": payload.get("metro_score", 0),
                "hs": payload.get("hospital_score", 0),
                "ss": payload.get("school_score", 0),
                "ws": payload.get("walkability_score", 0),
                "media": payload.get("media_count", 0),
                "status": payload.get("status", "available"),
                "tags": json.dumps(payload.get("tags", [])),
                "images": ",".join(payload.get("images", [])) if isinstance(payload.get("images"), list) else payload.get("images", ""),
                "locality": payload.get("locality") or (payload.get("address", "").split(",")[0] if payload.get("address") else ""),
                "bedrooms": payload.get("bedrooms", 0),
                "bathrooms": payload.get("bathrooms", 0),
                "furnishing": payload.get("furnishing", "")
            })
            conn.commit()

        # Invalidate cached search results for this property's city
        try:
            import shared_redis
            shared_redis.invalidate_search_cache()
        except Exception:
            pass

        logger.info(f"[Index Worker] ✅ Indexed property {pid}")
        return True

    except Exception as e:
        logger.error(f"[Index Worker] ❌ Failed to index property {pid}: {e}")
        return False


def _delete_property(payload: dict) -> bool:
    """Mark property as deleted/unavailable in the search index."""
    pid = payload.get("property_id") or payload.get("id")
    if not pid:
        return False
    try:
        import shared_database
        from sqlalchemy import text
        with shared_database.sync_engine.connect() as conn:
            conn.execute(text("""
                UPDATE search.property_index
                SET status = 'unavailable', updated_at = NOW()
                WHERE property_id = :pid
            """), {"pid": pid})
            conn.commit()
        logger.info(f"[Index Worker] Marked property {pid} as unavailable")
        return True
    except Exception as e:
        logger.error(f"[Index Worker] Failed to delete property {pid}: {e}")
        return False


def _update_locality_score(payload: dict) -> bool:
    """Update locality scores in index when geo service computes new scores."""
    lat = payload.get("lat")
    lng = payload.get("lng")
    scores = payload.get("scores", {})
    if not lat or not lng:
        return False

    try:
        import shared_database
        from sqlalchemy import text
        with shared_database.sync_engine.connect() as conn:
            conn.execute(text("""
                UPDATE search.property_index
                SET locality_score = :ls,
                    metro_score = :ms,
                    hospital_score = :hs,
                    school_score = :ss,
                    walkability_score = :ws,
                    updated_at = NOW()
                WHERE ABS(lat - :lat) < 0.01 AND ABS(lng - :lng) < 0.01
            """), {
                "ls": scores.get("overall_score", 0),
                "ms": scores.get("metro_score", 0),
                "hs": scores.get("hospital_score", 0),
                "ss": scores.get("school_score", 0),
                "ws": scores.get("walkability_score", 0),
                "lat": lat,
                "lng": lng,
            })
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"[Index Worker] Locality score update failed: {e}")
        return False


def _on_message(channel, method, properties, body):
    """Handle incoming RabbitMQ index event."""
    routing_key = method.routing_key
    try:
        payload = json.loads(body)
    except Exception:
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    try:
        if routing_key in ("property.created", "property.updated", "property.media_updated"):
            _upsert_property(payload)
        elif routing_key == "property.deleted":
            _delete_property(payload)
        elif routing_key == "locality_score_updated":
            _update_locality_score(payload)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"[Index Worker] Message processing failed: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def run_worker():
    logger.info("[Index Worker] Starting property index sync worker...")
    try:
        import pika
        RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        params = pika.URLParameters(RABBITMQ_URL)
        params.socket_timeout = 5.0

        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(
            queue="search_index_queue",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "rentora_dlx",
                "x-dead-letter-routing-key": "dlq.search_index",
            }
        )

        for rk in ROUTING_KEYS:
            channel.queue_bind(
                queue="search_index_queue",
                exchange="rentora_exchange",
                routing_key=rk,
            )

        channel.basic_qos(prefetch_count=10)
        channel.basic_consume(queue="search_index_queue", on_message_callback=_on_message)

        logger.info(f"[Index Worker] Consuming: {ROUTING_KEYS}")
        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info("[Index Worker] Shutting down...")
    except Exception as e:
        logger.error(f"[Index Worker] Failed to start: {e}")


if __name__ == "__main__":
    run_worker()
