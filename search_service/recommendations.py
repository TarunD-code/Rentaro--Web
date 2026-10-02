"""
Recommendation Engine — Priority 4 Rentora Search Intelligence
Content-based, collaborative, commute-based, and locality-affinity recommendations.
"""
import json
import math
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger("recommendations")

REC_SIMILAR_TTL   = 3600    # 1 hour cache for similar properties
REC_FOR_YOU_TTL   = 1800    # 30 min cache for personalized recs
REC_TRENDING_TTL  = 900     # 15 min cache for trending in locality
MAX_RECS          = 10


def _cache_get(key: str) -> Optional[list]:
    try:
        import shared_redis
        val = shared_redis.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


def _cache_set(key: str, data: list, ttl: int) -> None:
    try:
        import shared_redis
        shared_redis.set(key, json.dumps(data), ttl=ttl)
    except Exception:
        pass


def get_similar_properties(
    property_id: int,
    db: Session,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """
    Content-based: find properties with similar price band, type, amenities, locality score.
    """
    cache_key = f"rec:similar:{property_id}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        # Get base property
        base = db.execute(text("""
            SELECT property_id, price, property_type, city, locality_score,
                   commute_score, amenities, lat, lng
            FROM search.property_index
            WHERE property_id = :pid AND status = 'available'
        """), {"pid": property_id}).fetchone()

        if not base:
            return []

        price_low  = (base[1] or 0) * 0.7
        price_high = (base[1] or 0) * 1.3

        rows = db.execute(text("""
            SELECT property_id, title, address, price, property_type, lat, lng,
                   locality_score, commute_score, is_featured, is_verified,
                   media_count, view_count
            FROM search.property_index
            WHERE property_id <> :pid
              AND status = 'available'
              AND price BETWEEN :plo AND :phi
              AND (property_type = :ptype OR city = :city)
            ORDER BY ABS(locality_score - :ls) ASC, popularity_score DESC
            LIMIT :lim
        """), {
            "pid": property_id,
            "plo": price_low,
            "phi": price_high,
            "ptype": base[2],
            "city": base[3],
            "ls": base[4] or 0,
            "lim": limit,
        }).fetchall()

        results = _rows_to_dicts(rows)
        _cache_set(cache_key, results, REC_SIMILAR_TTL)
        return results

    except Exception as e:
        logger.error(f"Similar properties query failed: {e}")
        return []


def get_recommendations_for_user(
    user_id: str,
    db: Session,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Personalized recommendations: combines user's search history locality affinity
    and viewed properties to suggest properties.
    """
    cache_key = f"rec:user:{user_id}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        from . import analytics
        affinities = analytics.get_user_locality_affinity(user_id, db)

        if not affinities:
            # Fallback: return top popular available properties
            return get_popular_properties(db, limit=limit)

        top_queries = [a[0] for a in affinities[:3]]
        results = []

        for q in top_queries:
            rows = db.execute(text("""
                SELECT property_id, title, address, price, property_type, lat, lng,
                       locality_score, commute_score, is_featured, is_verified,
                       media_count, view_count
                FROM search.property_index
                WHERE status = 'available'
                  AND (LOWER(city) LIKE :q OR LOWER(address) LIKE :q OR LOWER(title) LIKE :q)
                ORDER BY locality_score DESC, popularity_score DESC
                LIMIT :lim
            """), {"q": f"%{q}%", "lim": limit // len(top_queries) + 2}).fetchall()

            for row in rows:
                pid = row[0]
                if pid not in {r["property_id"] for r in results}:
                    results.append(_row_to_dict(row))

        results = results[:limit]
        _cache_set(cache_key, results, REC_FOR_YOU_TTL)
        return results

    except Exception as e:
        logger.error(f"Personalized recommendations failed: {e}")
        return get_popular_properties(db, limit=limit)


def get_popular_properties(
    db: Session,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """Return most viewed/popular available properties."""
    cache_key = f"rec:popular:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        rows = db.execute(text("""
            SELECT property_id, title, address, price, property_type, lat, lng,
                   locality_score, commute_score, is_featured, is_verified,
                   media_count, view_count
            FROM search.property_index
            WHERE status = 'available'
            ORDER BY popularity_score DESC, view_count DESC, locality_score DESC
            LIMIT :lim
        """), {"lim": limit}).fetchall()

        results = _rows_to_dicts(rows)
        _cache_set(cache_key, results, REC_TRENDING_TTL)
        return results
    except Exception as e:
        logger.error(f"Popular properties query failed: {e}")
        return []


def get_trending_in_locality(
    locality: str,
    db: Session,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """Return trending properties in a specific locality."""
    cache_key = f"rec:trending:{locality.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        rows = db.execute(text("""
            SELECT property_id, title, address, price, property_type, lat, lng,
                   locality_score, commute_score, is_featured, is_verified,
                   media_count, view_count
            FROM search.property_index
            WHERE status = 'available'
              AND (LOWER(city) LIKE :loc OR LOWER(address) LIKE :loc)
            ORDER BY view_count DESC, contact_count DESC, locality_score DESC
            LIMIT :lim
        """), {"loc": f"%{locality.lower()}%", "lim": limit}).fetchall()

        results = _rows_to_dicts(rows)
        _cache_set(cache_key, results, REC_TRENDING_TTL)
        return results
    except Exception as e:
        logger.error(f"Trending in locality query failed: {e}")
        return []


def get_commute_recommendations(
    office_name: str,
    db: Session,
    max_commute_min: int = 30,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Return properties near a known office hub with good commute scores.
    """
    cache_key = f"rec:commute:{office_name.lower()}:{max_commute_min}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        # Get office coordinates from autocomplete_index
        office_row = db.execute(text("""
            SELECT lat, lng FROM search.autocomplete_index
            WHERE LOWER(term) LIKE :office AND term_type = 'office_hub'
            LIMIT 1
        """), {"office": f"%{office_name.lower()}%"}).fetchone()

        if not office_row or not office_row[0]:
            return get_popular_properties(db, limit=limit)

        o_lat, o_lng = office_row[0], office_row[1]
        radius_m = max_commute_min * 600  # ~35 km/h driving

        rows = db.execute(text("""
            SELECT pi.property_id, pi.title, pi.address, pi.price, pi.property_type,
                   pi.lat, pi.lng, pi.locality_score, pi.commute_score,
                   pi.is_featured, pi.is_verified, pi.media_count, pi.view_count
            FROM search.property_index pi
            JOIN property.properties p ON p.id = pi.property_id
            WHERE pi.status = 'available'
              AND p.geom IS NOT NULL
              AND ST_DWithin(
                  p.geom::geography,
                  ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                  :radius
              )
            ORDER BY pi.commute_score DESC, pi.locality_score DESC
            LIMIT :lim
        """), {"lat": o_lat, "lng": o_lng, "radius": radius_m, "lim": limit}).fetchall()

        results = _rows_to_dicts(rows)
        _cache_set(cache_key, results, REC_FOR_YOU_TTL)
        return results
    except Exception as e:
        logger.warning(f"Commute recommendations failed (PostGIS may be unavailable): {e}")
        return get_popular_properties(db, limit=limit)


def get_people_also_viewed(
    property_id: int,
    db: Session,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """
    Collaborative filtering: users who viewed this property also viewed...
    Uses co-view pairs from analytics_events.
    """
    cache_key = f"rec:pav:{property_id}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        # Find sessions that viewed this property
        rows = db.execute(text("""
            SELECT DISTINCT ae2.property_id, pi.title, pi.address, pi.price, pi.property_type,
                   pi.lat, pi.lng, pi.locality_score, pi.commute_score,
                   pi.is_featured, pi.is_verified, pi.media_count, pi.view_count
            FROM search.analytics_events ae1
            JOIN search.analytics_events ae2
              ON ae1.session_id = ae2.session_id
              AND ae2.property_id <> :pid
              AND ae2.event_type = 'analytics.property_viewed'
            JOIN search.property_index pi ON pi.property_id = ae2.property_id
            WHERE ae1.property_id = :pid
              AND ae1.event_type = 'analytics.property_viewed'
              AND pi.status = 'available'
            GROUP BY ae2.property_id, pi.title, pi.address, pi.price, pi.property_type,
                     pi.lat, pi.lng, pi.locality_score, pi.commute_score,
                     pi.is_featured, pi.is_verified, pi.media_count, pi.view_count
            ORDER BY COUNT(*) DESC
            LIMIT :lim
        """), {"pid": property_id, "lim": limit}).fetchall()

        results = _rows_to_dicts(rows)
        if not results:
            results = get_similar_properties(property_id, db, limit=limit)

        _cache_set(cache_key, results, REC_SIMILAR_TTL)
        return results
    except Exception as e:
        logger.warning(f"People also viewed failed: {e}")
        return get_similar_properties(property_id, db, limit=limit)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> Dict[str, Any]:
    return {
        "property_id": row[0], "title": row[1], "address": row[2],
        "price": row[3], "property_type": row[4], "lat": row[5], "lng": row[6],
        "locality_score": row[7], "commute_score": row[8],
        "is_featured": row[9], "is_verified": row[10],
        "media_count": row[11], "view_count": row[12],
    }


def _rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [_row_to_dict(r) for r in rows]
