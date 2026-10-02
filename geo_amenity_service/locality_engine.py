"""
Rentora Smart Locality Engine™
Weighted multi-category locality and property scoring system.
"""
import math
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("locality_engine")

# Default scoring weights (tenant can override)
DEFAULT_WEIGHTS = {
    "metro_connectivity": 0.15,
    "hospital_access": 0.10,
    "school_access": 0.10,
    "grocery_access": 0.10,
    "office_connectivity": 0.15,
    "park_access": 0.05,
    "lifestyle": 0.10,
    "walkability": 0.10,
    "transit_access": 0.10,
    "family_friendly": 0.05,
}

# Radius thresholds for score calculation (meters)
SCORE_THRESHOLDS = {
    "metro": {"excellent": 500, "good": 1000, "fair": 2000, "poor": 5000},
    "hospital": {"excellent": 1000, "good": 2000, "fair": 3000, "poor": 5000},
    "school": {"excellent": 500, "good": 1000, "fair": 2000, "poor": 5000},
    "grocery": {"excellent": 300, "good": 500, "fair": 1000, "poor": 2000},
    "office": {"excellent": 1000, "good": 3000, "fair": 5000, "poor": 10000},
    "park": {"excellent": 300, "good": 500, "fair": 1000, "poor": 2000},
    "restaurant": {"excellent": 300, "good": 500, "fair": 1000, "poor": 2000},
    "bus": {"excellent": 200, "good": 400, "fair": 800, "poor": 1500},
    "gym": {"excellent": 500, "good": 1000, "fair": 2000, "poor": 3000},
}


def compute_category_score(distances: List[float], category: str) -> float:
    """
    Compute a 0-10 score for a given category based on distances to nearest amenities.
    Uses exponential decay from thresholds.
    """
    if not distances:
        return 0.0

    thresholds = SCORE_THRESHOLDS.get(category, {"excellent": 500, "good": 1000, "fair": 2000, "poor": 5000})

    # Use the closest amenity distance
    min_dist = min(distances)

    if min_dist <= thresholds["excellent"]:
        score = 9.0 + (1.0 * (1 - min_dist / thresholds["excellent"]))
    elif min_dist <= thresholds["good"]:
        ratio = (min_dist - thresholds["excellent"]) / (thresholds["good"] - thresholds["excellent"])
        score = 7.0 + 2.0 * (1 - ratio)
    elif min_dist <= thresholds["fair"]:
        ratio = (min_dist - thresholds["good"]) / (thresholds["fair"] - thresholds["good"])
        score = 5.0 + 2.0 * (1 - ratio)
    elif min_dist <= thresholds["poor"]:
        ratio = (min_dist - thresholds["fair"]) / (thresholds["poor"] - thresholds["fair"])
        score = 2.0 + 3.0 * (1 - ratio)
    else:
        score = max(0.0, 2.0 * (1 - (min_dist - thresholds["poor"]) / thresholds["poor"]))

    # Density bonus: more amenities nearby = small boost
    density_bonus = min(0.5, len(distances) * 0.05)

    return round(min(10.0, score + density_bonus), 1)


def compute_locality_score(
    amenity_distances: Dict[str, List[float]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute a comprehensive locality score from amenity distance data.

    amenity_distances: { "metro": [500, 1200], "hospital": [800], ... }
    weights: custom tenant preference weights (optional)

    Returns: {
        "metro_score": 9.2,
        "hospital_score": 8.7,
        "school_score": 7.5,
        "grocery_score": 8.1,
        "office_score": 9.5,
        "park_score": 6.0,
        "lifestyle_score": 7.8,
        "walkability_score": 8.2,
        "transit_score": 8.8,
        "family_score": 7.2,
        "overall_score": 8.4
    }
    """
    w = weights or DEFAULT_WEIGHTS

    # Category-to-score mapping
    category_scores = {}
    for cat in ["metro", "hospital", "school", "grocery", "office", "park", "restaurant", "bus", "gym"]:
        dists = amenity_distances.get(cat, [])
        category_scores[cat] = compute_category_score(dists, cat)

    # Composite named scores
    metro_score = category_scores.get("metro", 0)
    hospital_score = category_scores.get("hospital", 0)
    school_score = category_scores.get("school", 0)
    grocery_score = category_scores.get("grocery", 0)
    office_score = category_scores.get("office", 0)
    park_score = category_scores.get("park", 0)

    # Composite derived scores
    lifestyle_score = round((category_scores.get("restaurant", 0) * 0.5 + category_scores.get("gym", 0) * 0.3 + park_score * 0.2), 1)
    transit_score = round((metro_score * 0.6 + category_scores.get("bus", 0) * 0.4), 1)
    walkability_score = round((grocery_score * 0.3 + transit_score * 0.3 + park_score * 0.2 + lifestyle_score * 0.2), 1)
    family_score = round((school_score * 0.3 + hospital_score * 0.2 + park_score * 0.2 + grocery_score * 0.15 + walkability_score * 0.15), 1)

    # Weighted overall
    overall = (
        metro_score * w.get("metro_connectivity", 0.15) +
        hospital_score * w.get("hospital_access", 0.10) +
        school_score * w.get("school_access", 0.10) +
        grocery_score * w.get("grocery_access", 0.10) +
        office_score * w.get("office_connectivity", 0.15) +
        park_score * w.get("park_access", 0.05) +
        lifestyle_score * w.get("lifestyle", 0.10) +
        walkability_score * w.get("walkability", 0.10) +
        transit_score * w.get("transit_access", 0.10) +
        family_score * w.get("family_friendly", 0.05)
    )

    return {
        "metro_score": metro_score,
        "hospital_score": hospital_score,
        "school_score": school_score,
        "grocery_score": grocery_score,
        "office_score": office_score,
        "park_score": park_score,
        "lifestyle_score": lifestyle_score,
        "walkability_score": walkability_score,
        "transit_score": transit_score,
        "family_score": family_score,
        "overall_score": round(overall, 1),
    }


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in meters."""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
