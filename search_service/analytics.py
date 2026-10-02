"""
Behavioral Analytics Engine — Priority 4 Rentora Search Intelligence
Tracks property views, clicks, searches, contacts, and bookings
via async RabbitMQ publishing with Redis hot-cache aggregation.
"""
import json
import time
import hashlib
import logging
import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("analytics")

# Analytics event types
EVENT_PROPERTY_VIEWED   = "analytics.property_viewed"
EVENT_PROPERTY_CLICKED  = "analytics.property_clicked"
EVENT_SEARCH_PERFORMED  = "analytics.search_performed"
EVENT_CONTACT_INITIATED = "analytics.contact_initiated"
EVENT_FAVORITE_TOGGLED  = "analytics.favorite_toggled"
EVENT_VISIT_BOOKED      = "analytics.visit_booked"
EVENT_PAGE_VIEW         = "analytics.page_view"

# Redis keys
POPULARITY_ZSET = "search:popular"
DAILY_VIEWS_KEY = "analytics:daily_views:{date}:{property_id}"
SESSION_DWELL_KEY = "analytics:session:{session_id}"


def _get_ip_hash(ip: Optional[str]) -> Optional[str]:
    """Hash IP for privacy compliance."""
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _get_session_id(user_id: Optional[str], ip: Optional[str]) -> str:
    """Generate a session identifier."""
    raw = f"{user_id or 'anon'}:{ip or 'unknown'}:{datetime.date.today()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def track_event(
    event_type: str,
    payload: Dict[str, Any],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip: Optional[str] = None,
) -> bool:
    """
    Publish an analytics event to RabbitMQ asynchronously.
    Also updates Redis popularity counters immediately for hot-path ranking.
    """
    event = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id or _get_session_id(user_id, ip),
        "ip_hash": _get_ip_hash(ip),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        **payload,
    }

    # Immediate Redis update for hot-path popularity
    property_id = payload.get("property_id")
    if property_id and event_type in (EVENT_PROPERTY_VIEWED, EVENT_PROPERTY_CLICKED):
        try:
            import shared_redis
            client = shared_redis._get_redis_client()
            if client:
                client.zincrby(POPULARITY_ZSET, 1, str(property_id))
        except Exception as e:
            logger.debug(f"Redis popularity update failed: {e}")

    # Publish to RabbitMQ
    try:
        import shared_event_broker
        shared_event_broker.publish_event(
            event_type,
            event,
            "search_service",
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to publish analytics event {event_type}: {e}")
        return False


def track_property_view(
    property_id: int,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip: Optional[str] = None,
    source: str = "search",
) -> bool:
    return track_event(
        EVENT_PROPERTY_VIEWED,
        {"property_id": property_id, "source": source},
        user_id=user_id,
        session_id=session_id,
        ip=ip,
    )


def track_search(
    query: str,
    filters: Dict[str, Any],
    result_count: int,
    user_id: Optional[str] = None,
    ip: Optional[str] = None,
) -> bool:
    return track_event(
        EVENT_SEARCH_PERFORMED,
        {
            "search_query": query,
            "filters_json": json.dumps(filters),
            "result_count": result_count,
        },
        user_id=user_id,
        ip=ip,
    )


def get_property_popularity(property_id: int) -> float:
    """Get current popularity score for a property from Redis."""
    try:
        import shared_redis
        client = shared_redis._get_redis_client()
        if client:
            score = client.zscore(POPULARITY_ZSET, str(property_id))
            return float(score or 0)
    except Exception:
        pass
    return 0.0


def get_user_search_history(user_id: str, db) -> list:
    """Retrieve user's recent search history from the database."""
    try:
        from sqlalchemy import text
        rows = db.execute(text("""
            SELECT query, filters_json, searched_at
            FROM search.search_history
            WHERE user_id = :uid
            ORDER BY searched_at DESC
            LIMIT 10
        """), {"uid": user_id}).fetchall()
        return [{"query": r[0], "filters": r[1], "at": str(r[2])} for r in rows]
    except Exception:
        return []


def get_user_locality_affinity(user_id: str, db) -> list:
    """
    Extract top localities from user's search history for personalization.
    """
    history = get_user_search_history(user_id, db)
    locality_counts: Dict[str, int] = {}
    for h in history:
        q = h.get("query", "").lower()
        if q:
            locality_counts[q] = locality_counts.get(q, 0) + 1
    return sorted(locality_counts.items(), key=lambda x: -x[1])[:5]
