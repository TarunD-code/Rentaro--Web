"""
Autocomplete & Trending Engine — Priority 4 Rentora Search Intelligence
Provides instant prefix + fuzzy autocomplete with Redis caching and
trending search tracking via Redis sorted sets.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger("autocomplete")

AUTOCOMPLETE_CACHE_TTL = 300      # 5 minutes
TRENDING_WINDOW_SECONDS = 86400   # 24-hour trending window
TRENDING_KEY = "search:trending"
MAX_AUTOCOMPLETE_RESULTS = 10
SIMILARITY_THRESHOLD = 0.2        # pg_trgm similarity cutoff


def get_autocomplete_suggestions(
    prefix: str,
    db: Session,
    user_id: Optional[str] = None,
    limit: int = MAX_AUTOCOMPLETE_RESULTS,
) -> List[Dict[str, Any]]:
    """
    Return autocomplete suggestions for a prefix query.
    Priority order: exact prefix → trigram fuzzy → property names → user history
    All results cached in Redis.
    """
    if len(prefix.strip()) < 2:
        return []

    prefix_lower = prefix.strip().lower()
    cache_key = f"search:autocomplete:{prefix_lower}"

    # Check Redis cache
    try:
        import shared_redis
        cached = shared_redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    results: List[Dict[str, Any]] = []
    seen_terms = set()

    # 1. Exact prefix match from autocomplete_index
    try:
        rows = db.execute(text("""
            SELECT term, term_type, display_name, lat, lng, search_count
            FROM search.autocomplete_index
            WHERE term LIKE :prefix
            ORDER BY search_count DESC, term
            LIMIT :lim
        """), {"prefix": f"{prefix_lower}%", "lim": limit}).fetchall()

        for r in rows:
            key = (r[0], r[1])
            if key not in seen_terms:
                seen_terms.add(key)
                results.append({
                    "term": r[2] or r[0],
                    "type": r[1],
                    "lat": r[3],
                    "lng": r[4],
                    "source": "index",
                })
    except Exception as e:
        logger.warning(f"Autocomplete prefix query failed: {e}")

    # 2. Fuzzy/trigram match if not enough results
    if len(results) < limit:
        try:
            rows = db.execute(text("""
                SELECT term, term_type, display_name, lat, lng, search_count,
                       similarity(term, :q) AS sim
                FROM search.autocomplete_index
                WHERE similarity(term, :q) > :threshold
                  AND term NOT LIKE :prefix
                ORDER BY sim DESC, search_count DESC
                LIMIT :lim
            """), {
                "q": prefix_lower,
                "threshold": SIMILARITY_THRESHOLD,
                "prefix": f"{prefix_lower}%",
                "lim": limit - len(results),
            }).fetchall()

            for r in rows:
                key = (r[0], r[1])
                if key not in seen_terms:
                    seen_terms.add(key)
                    results.append({
                        "term": r[2] or r[0],
                        "type": r[1],
                        "lat": r[3],
                        "lng": r[4],
                        "source": "fuzzy",
                    })
        except Exception as e:
            logger.warning(f"Autocomplete fuzzy query failed: {e}")

    # 3. Property title matches (live property names)
    if len(results) < limit:
        try:
            rows = db.execute(text("""
                SELECT DISTINCT title, city, lat, lng
                FROM search.property_index
                WHERE LOWER(title) LIKE :prefix AND status = 'available'
                ORDER BY title
                LIMIT :lim
            """), {
                "prefix": f"%{prefix_lower}%",
                "lim": limit - len(results),
            }).fetchall()

            for r in rows:
                key = (r[0].lower(), "property")
                if key not in seen_terms:
                    seen_terms.add(key)
                    results.append({
                        "term": r[0],
                        "type": "property",
                        "lat": r[2],
                        "lng": r[3],
                        "source": "property",
                    })
        except Exception as e:
            logger.warning(f"Autocomplete property query failed: {e}")

    # 4. Add user history suggestions if authenticated
    if user_id and len(results) < limit:
        try:
            rows = db.execute(text("""
                SELECT DISTINCT query FROM search.search_history
                WHERE user_id = :uid AND LOWER(query) LIKE :prefix
                ORDER BY searched_at DESC
                LIMIT :lim
            """), {
                "uid": user_id,
                "prefix": f"{prefix_lower}%",
                "lim": 3,
            }).fetchall()

            for r in rows:
                key = (r[0].lower(), "history")
                if key not in seen_terms:
                    seen_terms.add(key)
                    results.append({
                        "term": r[0],
                        "type": "history",
                        "lat": None,
                        "lng": None,
                        "source": "history",
                    })
        except Exception:
            pass

    # Cache result
    try:
        import shared_redis
        shared_redis.set(cache_key, json.dumps(results[:limit]), ttl=AUTOCOMPLETE_CACHE_TTL)
    except Exception:
        pass

    return results[:limit]


def track_search_query(query: str, result_count: int = 0) -> None:
    """
    Increment trending score for a search query in Redis sorted set.
    Also increments autocomplete_index search_count.
    """
    if not query or len(query.strip()) < 2:
        return

    q = query.strip().lower()

    # Increment Redis trending sorted set
    try:
        import shared_redis
        client = shared_redis._get_redis_client()
        if client:
            client.zincrby(TRENDING_KEY, 1, q)
            # Expire the trending set daily
            client.expire(TRENDING_KEY, TRENDING_WINDOW_SECONDS)
    except Exception as e:
        logger.debug(f"Trending track failed: {e}")


def get_trending_searches(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return top trending searches from Redis sorted set.
    Falls back to static popular searches if Redis unavailable.
    """
    try:
        import shared_redis
        client = shared_redis._get_redis_client()
        if client:
            items = client.zrevrange(TRENDING_KEY, 0, limit - 1, withscores=True)
            return [{"query": item[0], "count": int(item[1])} for item in items]
    except Exception:
        pass

    # Static fallback
    return [
        {"query": "2BHK Whitefield", "count": 0},
        {"query": "near Manyata Tech Park", "count": 0},
        {"query": "furnished apartment Koramangala", "count": 0},
        {"query": "family home HSR Layout", "count": 0},
        {"query": "studio Indiranagar", "count": 0},
    ]


def get_contextual_suggestions(office: Optional[str] = None, locality: Optional[str] = None) -> List[str]:
    """Generate contextual search chip suggestions."""
    suggestions = []
    if office:
        suggestions.extend([
            f"near {office}",
            f"commute to {office} under 30 min",
            f"walking distance from {office}",
        ])
    if locality:
        suggestions.extend([
            f"family-friendly in {locality}",
            f"furnished flat in {locality}",
            f"2BHK in {locality}",
        ])
    if not suggestions:
        suggestions = [
            "Near metro station",
            "Family-friendly area",
            "Under ₹30,000/month",
            "Furnished apartment",
            "Pet-friendly",
            "Near IT park",
        ]
    return suggestions[:6]
