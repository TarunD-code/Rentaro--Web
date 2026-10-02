"""
Ranking Engine — Priority 4 Rentora Search Intelligence
Combines text relevance, geo proximity, locality scores, behavioral signals,
media quality, and owner quality into a unified final_score.
"""
import logging
import math
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ranking_engine")

# ─── DEFAULT RANKING WEIGHTS ──────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "text_relevance": 0.25,
    "locality_score": 0.20,
    "commute_score":  0.15,
    "freshness":      0.10,
    "engagement":     0.10,
    "amenity_score":  0.10,
    "media_quality":  0.05,
    "owner_quality":  0.05,
}

# Ranking profiles adjust the base weights
RANKING_PROFILES: Dict[str, Dict[str, float]] = {
    "family": {
        "text_relevance": 0.15,
        "locality_score": 0.25,   # schools, hospitals, parks matter more
        "commute_score":  0.10,
        "freshness":      0.05,
        "engagement":     0.10,
        "amenity_score":  0.15,   # pool, park, garden
        "media_quality":  0.10,
        "owner_quality":  0.10,
    },
    "student": {
        "text_relevance": 0.20,
        "locality_score": 0.15,
        "commute_score":  0.20,   # closer to college/transport
        "freshness":      0.15,
        "engagement":     0.10,
        "amenity_score":  0.05,
        "media_quality":  0.05,
        "owner_quality":  0.10,
    },
    "it_professional": {
        "text_relevance": 0.20,
        "locality_score": 0.15,
        "commute_score":  0.30,   # office proximity is #1
        "freshness":      0.05,
        "engagement":     0.10,
        "amenity_score":  0.05,
        "media_quality":  0.05,
        "owner_quality":  0.10,
    },
    "luxury": {
        "text_relevance": 0.15,
        "locality_score": 0.20,
        "commute_score":  0.05,
        "freshness":      0.05,
        "engagement":     0.15,
        "amenity_score":  0.20,   # premium amenities (gym, pool, concierge)
        "media_quality":  0.15,   # high-quality photos signal premium
        "owner_quality":  0.05,
    },
    "short_stay": {
        "text_relevance": 0.20,
        "locality_score": 0.15,
        "commute_score":  0.15,
        "freshness":      0.20,   # recent listings preferred
        "engagement":     0.15,
        "amenity_score":  0.10,
        "media_quality":  0.05,
        "owner_quality":  0.00,
    },
}

# ─── BOOST MULTIPLIERS ────────────────────────────────────────────────────────

def compute_boost(prop: Dict[str, Any]) -> float:
    """
    Compute a dynamic boost multiplier (1.0 = neutral, max ~1.5).
    Boosts for: featured, verified, high engagement, good media, quick responder.
    """
    boost = 1.0
    if prop.get("is_featured"):
        boost += 0.20
    if prop.get("is_verified"):
        boost += 0.10
    if prop.get("owner_verified"):
        boost += 0.05
    # High view count boost (log scale)
    views = prop.get("view_count", 0) or 0
    boost += min(0.08, math.log1p(views) * 0.01)
    # High contact count boost
    contacts = prop.get("contact_count", 0) or 0
    boost += min(0.05, math.log1p(contacts) * 0.01)
    # Good rating boost
    rating = prop.get("avg_rating", 0) or 0
    if rating >= 4.5:
        boost += 0.07
    elif rating >= 4.0:
        boost += 0.04
    # Good media count
    media = prop.get("media_count", 0) or 0
    if media >= 5:
        boost += 0.05
    elif media >= 2:
        boost += 0.02

    return round(min(boost, 1.5), 3)


# ─── INDIVIDUAL SIGNAL SCORES ─────────────────────────────────────────────────

def freshness_score(prop: Dict[str, Any]) -> float:
    """Score based on how recently the property was indexed/updated (0-1)."""
    import datetime
    ts = prop.get("updated_at") or prop.get("indexed_at")
    if not ts:
        return 0.5
    if isinstance(ts, str):
        try:
            ts = datetime.datetime.fromisoformat(ts)
        except Exception:
            return 0.5
    age_hours = (datetime.datetime.utcnow() - ts.replace(tzinfo=None)).total_seconds() / 3600
    # Freshness decays: < 24h = 1.0, < 72h = 0.8, < 1 week = 0.6, older = decay
    if age_hours < 24:
        return 1.0
    elif age_hours < 72:
        return 0.8
    elif age_hours < 168:
        return 0.6
    elif age_hours < 720:
        return 0.4
    else:
        return max(0.1, 1.0 - (age_hours / 8760) * 0.9)


def engagement_score(prop: Dict[str, Any]) -> float:
    """Normalize engagement metrics to 0-1."""
    views = prop.get("view_count", 0) or 0
    contacts = prop.get("contact_count", 0) or 0
    favorites = prop.get("favorite_count", 0) or 0
    popularity = prop.get("popularity_score", 0) or 0

    raw = (math.log1p(views) * 0.4 + math.log1p(contacts) * 0.35 +
           math.log1p(favorites) * 0.25) + (popularity * 0.1)
    return round(min(1.0, raw / 10.0), 3)


def media_quality_score(prop: Dict[str, Any]) -> float:
    """Score media count as proxy for quality (0-1)."""
    media = prop.get("media_count", 0) or 0
    if media >= 8:
        return 1.0
    elif media >= 5:
        return 0.8
    elif media >= 3:
        return 0.6
    elif media >= 1:
        return 0.3
    return 0.0


def owner_quality_score(prop: Dict[str, Any]) -> float:
    """Aggregate owner quality from rating and verification."""
    rating = prop.get("avg_rating", 0) or 0
    verified = 1.0 if prop.get("owner_verified") else 0.0
    score = (rating / 5.0) * 0.7 + verified * 0.3
    return round(min(1.0, score), 3)


def amenity_signal_score(prop: Dict[str, Any]) -> float:
    """Use stored amenity/locality scores as signal (0-1)."""
    metro = (prop.get("metro_score") or 0) / 10.0
    hospital = (prop.get("hospital_score") or 0) / 10.0
    school = (prop.get("school_score") or 0) / 10.0
    walkability = (prop.get("walkability_score") or 0) / 10.0
    return round((metro * 0.3 + hospital * 0.2 + school * 0.2 + walkability * 0.3), 3)


# ─── MAIN RANKING FUNCTION ────────────────────────────────────────────────────

def rank_properties(
    properties: List[Dict[str, Any]],
    text_relevance_scores: Optional[Dict[int, float]] = None,
    profile: str = "default",
) -> List[Dict[str, Any]]:
    """
    Apply the ranking engine to a list of property dicts.

    text_relevance_scores: map of property_id → ts_rank score (0-1)
    profile: one of default | family | student | it_professional | luxury | short_stay

    Returns properties sorted by final_score descending.
    """
    weights = RANKING_PROFILES.get(profile, DEFAULT_WEIGHTS)
    scored = []

    for prop in properties:
        pid = prop.get("property_id") or prop.get("id")
        tr = 0.0
        if text_relevance_scores and pid in text_relevance_scores:
            tr = min(1.0, text_relevance_scores[pid])

        ls = min(1.0, (prop.get("locality_score") or 0) / 10.0)
        cs = min(1.0, (prop.get("commute_score") or 0) / 10.0)
        fs = freshness_score(prop)
        es = engagement_score(prop)
        ams = amenity_signal_score(prop)
        mq = media_quality_score(prop)
        oq = owner_quality_score(prop)
        boost = compute_boost(prop)

        raw_score = (
            tr  * weights["text_relevance"] +
            ls  * weights["locality_score"] +
            cs  * weights["commute_score"] +
            fs  * weights["freshness"] +
            es  * weights["engagement"] +
            ams * weights["amenity_score"] +
            mq  * weights["media_quality"] +
            oq  * weights["owner_quality"]
        )

        final_score = round(raw_score * boost, 4)

        prop["_score"] = final_score
        prop["_signals"] = {
            "text_relevance": round(tr, 3),
            "locality_score": round(ls, 3),
            "commute_score": round(cs, 3),
            "freshness": round(fs, 3),
            "engagement": round(es, 3),
            "amenity": round(ams, 3),
            "media": round(mq, 3),
            "owner": round(oq, 3),
            "boost": boost,
        }
        scored.append(prop)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


def get_ranking_explanation(signals: Dict[str, float]) -> str:
    """Generate human-readable ranking explanation for UI tooltips."""
    reasons = []
    if signals.get("locality_score", 0) >= 0.7:
        reasons.append("Excellent locality")
    if signals.get("commute_score", 0) >= 0.7:
        reasons.append("Great commute access")
    if signals.get("text_relevance", 0) >= 0.7:
        reasons.append("Strong match")
    if signals.get("engagement", 0) >= 0.6:
        reasons.append("Highly popular")
    if signals.get("freshness", 0) >= 0.8:
        reasons.append("Recently listed")
    if signals.get("media", 0) >= 0.8:
        reasons.append("Rich media")
    if signals.get("boost", 1.0) >= 1.2:
        reasons.append("Premium listing")
    if not reasons:
        reasons.append("Good overall match")
    return " · ".join(reasons[:3])
