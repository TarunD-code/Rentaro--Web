"""
OpenRouteService (ORS) Client for commute intelligence.
Replaces the previous OSRM implementation.

ORS Directions API docs: https://openrouteservice.org/dev/#/api-docs/v2/directions
Profile endpoint: POST /v2/directions/{profile}/geojson
Returns a GeoJSON FeatureCollection — geometry is in features[0].geometry.

Tuple convention throughout this module: (lat, lng) — i.e. (latitude, longitude).
ORS expects coordinates as [longitude, latitude] in request bodies.
"""
import os
import httpx
import math
import json
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger("ors_client")

ORS_BASE_URL = "https://api.openrouteservice.org"
ORS_API_KEY: str = os.environ.get("ORS_API_KEY", "")

# Map internal mode names → ORS profile slugs
ORS_PROFILES: Dict[str, str] = {
    "driving": "driving-car",
    "walking":  "foot-walking",
    "cycling":  "cycling-regular",
}

# Realistic speed assumptions used when ORS is unavailable (km/h)
_FALLBACK_SPEEDS: Dict[str, float] = {
    "driving": 35.0,
    "walking":  5.0,
    "cycling": 15.0,
}


async def get_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str = "driving",
) -> Dict[str, Any]:
    """
    Calculate a road-network route between two points via ORS Directions API.

    Args:
        origin:      (latitude, longitude) of the start point.
        destination: (latitude, longitude) of the end point.
        mode:        one of 'driving', 'walking', 'cycling'.

    Returns a dict:
        {
            distance_km:  float,
            duration_min: float,
            mode:         str,
            geometry:     GeoJSON LineString   # coordinates are [lng, lat] per GeoJSON spec
        }

    Falls back to Haversine straight-line estimation if ORS is unavailable.
    """
    if mode not in ORS_PROFILES:
        mode = "driving"

    cache_key = (
        f"ors_route:{origin[0]:.4f},{origin[1]:.4f}"
        f":{destination[0]:.4f},{destination[1]:.4f}:{mode}"
    )

    # ── Redis cache check ──────────────────────────────────────────────────────
    try:
        import shared_redis
        cached = shared_redis.get(cache_key)
        if cached:
            logger.info(f"[ORS Cache HIT] {cache_key}")
            return json.loads(cached)
    except Exception:
        pass

    # ── ORS API call ───────────────────────────────────────────────────────────
    if ORS_API_KEY:
        profile = ORS_PROFILES[mode]
        # ORS expects [longitude, latitude] coordinate pairs
        payload = {
            "coordinates": [
                [origin[1],      origin[0]],       # [lng, lat] of origin
                [destination[1], destination[0]],  # [lng, lat] of destination
            ],
            "instructions": False,
            "geometry_simplify": False,
        }
        url = f"{ORS_BASE_URL}/v2/directions/{profile}/geojson"

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": ORS_API_KEY,
                        "Content-Type":  "application/json",
                        "Accept":        "application/json, application/geo+json",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    if features:
                        feature = features[0]
                        props = feature.get("properties", {})
                        summary = props.get("summary", {})

                        distance_km = round(summary.get("distance", 0) / 1000, 2)

                        # ORS returns accurate per-profile durations — use them directly.
                        # For walking/cycling the demo OSRM used to return car times;
                        # ORS does not have this problem, so we trust the summary.
                        duration_min = round(summary.get("duration", 0) / 60, 1)

                        geometry: Dict[str, Any] = feature.get("geometry", {})
                        # geometry.coordinates are already [lng, lat] — GeoJSON standard

                        result: Dict[str, Any] = {
                            "distance_km":  distance_km,
                            "duration_min": duration_min,
                            "mode":         mode,
                            "geometry":     geometry,
                        }

                        # Cache for 24 hours
                        try:
                            import shared_redis
                            shared_redis.set(cache_key, json.dumps(result), ttl=86400)
                        except Exception:
                            pass

                        logger.info(
                            f"[ORS] {mode} route {origin} → {destination}: "
                            f"{distance_km} km, {duration_min} min"
                        )
                        return result
                else:
                    logger.warning(
                        f"ORS API returned HTTP {resp.status_code}: {resp.text[:200]}"
                    )
        except httpx.TimeoutException:
            logger.warning("ORS API timed out — falling back to Haversine estimation.")
        except Exception as exc:
            logger.warning(f"ORS API call failed: {exc} — falling back to Haversine estimation.")
    else:
        logger.warning("ORS_API_KEY not configured — using Haversine estimation fallback.")

    # ── Haversine straight-line fallback ───────────────────────────────────────
    return _estimate_route(origin, destination, mode)


async def get_commute_matrix(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]],
    mode: str = "driving",
) -> List[Dict[str, Any]]:
    """
    Calculate commute times from one origin to multiple destinations.

    Args:
        origin:       (latitude, longitude)
        destinations: list of (latitude, longitude)
        mode:         'driving', 'walking', or 'cycling'
    """
    results: List[Dict[str, Any]] = []
    for dest in destinations:
        route = await get_route(origin, dest, mode)
        results.append({
            "destination": {"lat": dest[0], "lng": dest[1]},
            **route,
        })
    return results


def _estimate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str,
) -> Dict[str, Any]:
    """
    Haversine straight-line estimation used when ORS is unavailable.

    Inputs are (lat, lng) tuples.
    Geometry coordinates are emitted as [lng, lat] per GeoJSON spec so
    MapLibre can consume them without any transformation.
    """
    R = 6371.0  # Earth radius in km

    lat1_r = math.radians(origin[0])
    lon1_r = math.radians(origin[1])
    lat2_r = math.radians(destination[0])
    lon2_r = math.radians(destination[1])

    d_lat = lat2_r - lat1_r
    d_lon = lon2_r - lon1_r

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(d_lon / 2) ** 2
    )
    dist_km = R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    speed = _FALLBACK_SPEEDS.get(mode, 35.0)
    duration_min = round((dist_km / speed) * 60.0, 1)

    return {
        "distance_km":  round(dist_km, 2),
        "duration_min": duration_min,
        "mode":         mode,
        "geometry": {
            "type": "LineString",
            # [lng, lat] coordinate order required by GeoJSON / MapLibre
            "coordinates": [
                [origin[1],      origin[0]],
                [destination[1], destination[0]],
            ],
        },
        "estimated": True,
    }
