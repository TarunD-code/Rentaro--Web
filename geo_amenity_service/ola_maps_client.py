"""
Ola Maps (Krutrim Cloud) client for Rentora geo_amenity_service.

Replaces:
  - overpass_client.py  → Places Nearby Search API
  - ors_client.py       → Directions API

API base: https://api.olamaps.io
Docs:     https://maps.olakrutrim.com/krutrim/docs

Coordinate convention in this file:
  • All Python function signatures use (lat, lng) ordering.
  • Ola Maps Nearby Search location param: "{lat},{lng}"
  • Ola Maps Directions origin/destination param: "{lat},{lng}"
  • GeoJSON / MapLibre requires [lng, lat] — the polyline decoder produces
    (lat, lng) tuples which are explicitly reversed before returning.
"""
import os
import asyncio
import math
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

import httpx
import polyline as polyline_codec  # pip install polyline

logger = logging.getLogger("ola_maps_client")

# ── Configuration ─────────────────────────────────────────────────────────────

OLA_MAPS_API_KEY: str = os.environ.get("OLA_MAPS_API_KEY", "")
_BASE_URL = "https://api.olamaps.io"

# Categories that require a wider search radius
_LARGE_RADIUS_CATEGORIES: frozenset = frozenset(
    {"hospital", "office", "company", "tech_park", "coworking"}
)

# Per-category default radius (metres).
# 5 000 m for large categories; 2 000 m for everything else.
CATEGORY_DEFAULT_RADIUS: Dict[str, int] = {}  # populated lazily in get_category_radius()

# Map our internal category names → Ola Maps `types` query parameter values.
# Reference: https://maps.olakrutrim.com/krutrim/apidocs#tag/places-apis
CATEGORY_TO_OLA_TYPE: Dict[str, str] = {
    "school":       "school",
    "college":      "university",
    "university":   "university",
    "hospital":     "hospital",
    "clinic":       "clinic",
    "pharmacy":     "pharmacy",
    "metro":        "subway_station",
    "bus":          "bus_station",
    "bus_stop":     "bus_station",
    "bus_station":  "bus_station",
    "bus_depot":    "bus_station",
    "grocery":      "grocery_or_supermarket",
    "supermarket":  "supermarket",
    "park":         "park",
    "playground":   "park",
    "gym":          "gym",
    "fuel":         "gas_station",
    "restaurant":   "restaurant",
    "cafe":         "cafe",
    "office":       "office",
    "company":      "establishment",
    "tech_park":    "establishment",
    "coworking":    "establishment",
    "mall":         "shopping_mall",
    "atm":          "atm",
    "bank":         "bank",
}

# Fallback speed assumptions (km/h) used when Ola Maps routing is unavailable
_FALLBACK_SPEEDS: Dict[str, float] = {
    "driving": 35.0,
    "walking":  5.0,
    "cycling": 15.0,
}


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_category_radius(category: str) -> int:
    """Return the default search radius in metres for a given category."""
    return 5000 if category in _LARGE_RADIUS_CATEGORIES else 2000


# ── Places: Nearby Search ──────────────────────────────────────────────────────

async def fetch_nearby_amenities(
    lat: float,
    lng: float,
    category: str,
    radius: int,
) -> List[Dict[str, Any]]:
    """
    Fetch POIs from Ola Maps Nearby Search API for a single category.

    Args:
        lat:      Latitude of the search centre.
        lng:      Longitude of the search centre.
        category: Internal Rentora category name (e.g. 'hospital', 'park').
        radius:   Search radius in metres.

    Returns:
        List of dicts conforming to the frontend POI contract:
        [{ "osm_id", "name", "category", "lat", "lng", "subcategory", "tags" }]

    Raises:
        httpx.HTTPStatusError: on non-2xx responses (caller should catch).
    """
    if not OLA_MAPS_API_KEY:
        logger.warning("[OlaMaps] OLA_MAPS_API_KEY not set — skipping Places API call.")
        return []

    ola_type   = CATEGORY_TO_OLA_TYPE.get(category, category)
    request_id = str(uuid.uuid4())

    # ── Redis cache check (7-day TTL) ─────────────────────────────────────────
    # Key uses 3 d.p. coordinates (~111 m resolution) so nearby searches share
    # the same cache entry without creating excessive key fragmentation.
    cache_key = f"pois_{round(lat, 3)}_{round(lng, 3)}_{category}_{radius}"
    try:
        import shared_redis
        cached = shared_redis.get(cache_key)
        if cached:
            logger.info(f"[OlaMaps Places Cache HIT] {cache_key}")
            return json.loads(cached)
    except Exception:
        pass

    params: Dict[str, Any] = {
        "types":    ola_type,
        "location": f"{lat},{lng}",
        "radius":   radius,
        "api_key":  OLA_MAPS_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            resp = await client.get(
                f"{_BASE_URL}/places/v1/nearbysearch/advanced",
                params=params,
                headers={"X-Request-Id": request_id},
            )

        if resp.status_code != 200:
            logger.warning(
                f"[OlaMaps Places] HTTP {resp.status_code} for category '{category}': "
                f"{resp.text[:200]}"
            )
            return []

        data = resp.json()

        raw_places: List[Dict[str, Any]] = data.get("results") or data.get("predictions", [])

        # ── Pass 1: extract whatever coordinates are already inline ──────────
        # Separate the places that need hydration from those that don't so we
        # can fire all Detail API calls concurrently instead of sequentially.
        resolved:       List[Dict[str, Any]] = []   # fully-resolved place dicts
        needs_hydration: List[Dict[str, Any]] = []   # places missing coordinates

        for idx, place in enumerate(raw_places):
            name: str = (
                place.get("name")
                or place.get("structured_formatting", {}).get("main_text")
                or place.get("description", "")
                or f"{category.title()} (Unnamed)"
            )
            place_id: str  = place.get("place_id", f"ola_{request_id}_{idx}")
            distance_m: float = float(place.get("distance_meters", 0))

            place_lat: Optional[float] = None
            place_lng: Optional[float] = None

            geom = place.get("geometry", {})
            loc  = geom.get("location") or geom.get("loc") or {}
            if isinstance(loc, dict):
                place_lat = loc.get("lat") or loc.get("latitude")
                place_lng = loc.get("lng") or loc.get("lon") or loc.get("longitude")

            if place_lat is None:
                place_lat = place.get("lat") or place.get("latitude")
                place_lng = place.get("lng") or place.get("lon") or place.get("longitude")

            if place_lat is not None and place_lng is not None:
                resolved.append({
                    "osm_id":      place_id,
                    "name":        _normalize_name(name),
                    "category":    category,
                    "subcategory": next(iter(place.get("types", [])), None),
                    "lat":         float(place_lat),
                    "lng":         float(place_lng),
                    "distance_m":  int(distance_m),
                    "tags":        {},
                })
            else:
                needs_hydration.append({
                    "_place_id":   place_id,
                    "_name":       name,
                    "_distance_m": distance_m,
                    "_types":      place.get("types", []),
                })

        # ── Pass 2: concurrent Place Details hydration ────────────────────────
        # All Detail API calls fire simultaneously via asyncio.gather, cutting
        # worst-case latency from O(n × RTT) to O(1 × RTT).
        if needs_hydration:
            async def _hydrate(stub: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                pid = stub["_place_id"]
                try:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(8.0, connect=3.0)
                    ) as dc:
                        dr = await dc.get(
                            f"{_BASE_URL}/places/v1/details",
                            params={"place_id": pid, "api_key": OLA_MAPS_API_KEY},
                            headers={"X-Request-Id": str(uuid.uuid4())},
                        )
                    if dr.status_code == 200:
                        dl  = dr.json().get("result", {}).get("geometry", {}).get("location", {})
                        dlat = dl.get("lat")
                        dlng = dl.get("lng")
                        if dlat is not None and dlng is not None:
                            return {
                                "osm_id":      pid,
                                "name":        _normalize_name(stub["_name"]),
                                "category":    category,
                                "subcategory": next(iter(stub["_types"]), None),
                                "lat":         float(dlat),
                                "lng":         float(dlng),
                                "distance_m":  int(stub["_distance_m"]),
                                "tags":        {},
                            }
                        logger.warning(f"[OlaMaps PlaceDetails] No coords for place_id={pid}")
                    else:
                        logger.warning(
                            f"[OlaMaps PlaceDetails] HTTP {dr.status_code} for {pid}: {dr.text[:120]}"
                        )
                except httpx.RequestError as exc:
                    logger.error(f"[OlaMaps PlaceDetails] Network error for {pid}: {exc}")
                return None

            hydration_results = await asyncio.gather(
                *[_hydrate(stub) for stub in needs_hydration],
                return_exceptions=False,
            )
            resolved.extend(r for r in hydration_results if r is not None)

        results = resolved

        logger.info(
            f"[OlaMaps Places] '{category}' @ ({lat:.4f},{lng:.4f}) "
            f"r={radius}m → {len(results)} results "
            f"({len(needs_hydration)} hydrated concurrently)"
        )

        # ── Store in Redis for 7 days ─────────────────────────────────────────
        if results:
            try:
                import shared_redis
                shared_redis.set(cache_key, json.dumps(results), ttl=604800)
            except Exception:
                pass

        return results

    except httpx.RequestError as exc:
        logger.error(f"[OlaMaps Places] Network error for '{category}': {exc}")
        raise


async def fetch_amenities_by_category_radius(
    lat: float,
    lng: float,
    categories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch amenities using per-category radius rules via Ola Maps:
      - hospital / office family → 5 000 m (single pass)
      - all other categories     → 2 000 m, auto-expands to 5 000 m if empty

    Args:
        lat:        Search centre latitude.
        lng:        Search centre longitude.
        categories: Optional list of internal category names.
                    Defaults to all known categories.

    Returns:
        Merged, deduplicated list of POI dicts.
    """
    if categories is None:
        categories = list(CATEGORY_TO_OLA_TYPE.keys())

    all_results: List[Dict[str, Any]] = []
    seen_ids: set = set()

    for category in categories:
        if category not in CATEGORY_TO_OLA_TYPE:
            continue

        primary_radius = get_category_radius(category)
        # Large-radius categories: single pass at 5 000 m
        # Standard categories: try 2 000 m, expand to 5 000 m if empty
        radii_to_try: List[int] = (
            [primary_radius]
            if primary_radius >= 5000
            else [primary_radius, 5000]
        )

        category_results: List[Dict[str, Any]] = []

        for radius_m in radii_to_try:
            try:
                batch = await fetch_nearby_amenities(lat, lng, category, radius_m)
            except httpx.RequestError:
                break  # network failure — trigger fallback in caller

            # Deduplicate by osm_id (place_id)
            fresh = [p for p in batch if p["osm_id"] not in seen_ids]
            for p in fresh:
                seen_ids.add(p["osm_id"])

            if fresh:
                category_results = fresh
                break  # found results at this radius — no expansion needed

        all_results.extend(category_results)

    return all_results


# ── Routing: Directions ────────────────────────────────────────────────────────

async def get_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str = "driving",
) -> Dict[str, Any]:
    """
    Calculate a traffic-aware road route between two points via Ola Maps
    Directions API.

    Args:
        origin:      (latitude, longitude) of the start point.
        destination: (latitude, longitude) of the end point.
        mode:        Transport mode — currently 'driving' (Ola Maps supports
                     driving by default; walking/cycling fall back to estimation).

    Returns:
        {
            distance_km:  float,
            duration_min: float,
            mode:         str,
            geometry: {
                type: "LineString",
                coordinates: [[lng, lat], ...]  # GeoJSON / MapLibre standard
            }
        }

    Falls back to Haversine straight-line estimation if the API is unavailable.
    """
    if mode not in ("driving", "walking", "cycling"):
        mode = "driving"

    # Cache key uses 3 d.p. (≈111 m resolution) so routes from nearly-identical
    # origins/destinations share a single cache entry. Format matches the spec:
    # route_{src_lat}_{src_lng}_{dest_lat}_{dest_lng}_{mode}
    cache_key = (
        f"route_{origin[0]:.3f}_{origin[1]:.3f}"
        f"_{destination[0]:.3f}_{destination[1]:.3f}_{mode}"
    )

    # ── Redis cache ────────────────────────────────────────────────────────────
    try:
        import shared_redis
        cached = shared_redis.get(cache_key)
        if cached:
            logger.info(f"[OlaMaps Route Cache HIT] {cache_key}")
            return json.loads(cached)
    except Exception:
        pass

    # ── Ola Maps API call ──────────────────────────────────────────────────────
    if OLA_MAPS_API_KEY:
        # Ola Maps Directions: origin/destination as "lat,lng" strings
        params: Dict[str, Any] = {
            "origin":      f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "api_key":     OLA_MAPS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=3.0)) as client:
                resp = await client.post(
                    f"{_BASE_URL}/routing/v1/directions",
                    params=params,
                    headers={"X-Request-Id": str(uuid.uuid4())},
                )

            if resp.status_code == 200:
                data = resp.json()
                # Ola Maps response shape:
                # { "status": "SUCCESS", "routes": [{ "legs": [...], "overview_polyline": {"points": "..."}, ... }] }
                routes: List[Dict[str, Any]] = data.get("routes", [])

                if routes:
                    route = routes[0]

                    legs: List[Dict[str, Any]] = route.get("legs", [])
                    # Distance and duration — Ola Maps returns plain integers on each leg
                    # (not nested {"value": N} objects like Google Maps)
                    total_distance_m: float = sum(
                        leg.get("distance", 0) for leg in legs
                    )
                    total_duration_s: float = sum(
                        leg.get("duration", 0) for leg in legs
                    )

                    distance_km = round(total_distance_m / 1000.0, 2)
                    duration_min = round(total_duration_s / 60.0, 1)

                    # Decode the overview polyline into GeoJSON coordinates.
                    # Ola Maps returns overview_polyline as a plain encoded string
                    # (not a {"points": "..."} dict like Google Maps).
                    overview_raw = route.get("overview_polyline", "")
                    if isinstance(overview_raw, dict):
                        encoded_polyline: str = overview_raw.get("points", "")
                    else:
                        encoded_polyline = str(overview_raw)
                    geojson_coords = _decode_polyline_to_geojson(encoded_polyline)

                    # If overview_polyline is absent, fall back to step-level polylines
                    if not geojson_coords:
                        for leg in legs:
                            for step in leg.get("steps", []):
                                step_encoded = (
                                    step.get("polyline", {}).get("points", "")
                                )
                                geojson_coords.extend(
                                    _decode_polyline_to_geojson(step_encoded)
                                )

                    if geojson_coords:
                        result: Dict[str, Any] = {
                            "distance_km":  distance_km,
                            "duration_min": duration_min,
                            "mode":         mode,
                            "geometry": {
                                "type":        "LineString",
                                "coordinates": geojson_coords,
                            },
                        }

                        # Cache for 7 days — routes between fixed Bengaluru locations
                        # are stable; 604 800 s avoids redundant Ola Maps API calls.
                        try:
                            import shared_redis
                            shared_redis.set(cache_key, json.dumps(result), ttl=604800)
                        except Exception:
                            pass

                        logger.info(
                            f"[OlaMaps Route] {mode} {origin} → {destination}: "
                            f"{distance_km} km, {duration_min} min, "
                            f"{len(geojson_coords)} polyline points"
                        )
                        return result

                    logger.warning("[OlaMaps Route] Route returned but polyline is empty.")
                else:
                    logger.warning(
                        f"[OlaMaps Route] No routes in response: {resp.text[:300]}"
                    )
            else:
                logger.warning(
                    f"[OlaMaps Route] HTTP {resp.status_code}: {resp.text[:200]}"
                )

        except httpx.TimeoutException:
            logger.warning("[OlaMaps Route] Request timed out — falling back to Haversine.")
        except Exception as exc:
            logger.warning(f"[OlaMaps Route] Unexpected error: {exc} — falling back to Haversine.")
    else:
        logger.warning("[OlaMaps Route] OLA_MAPS_API_KEY not configured — using Haversine fallback.")

    # ── Haversine straight-line fallback ───────────────────────────────────────
    return _estimate_route(origin, destination, mode)


async def get_commute_matrix(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]],
    mode: str = "driving",
) -> List[Dict[str, Any]]:
    """
    Calculate routes from one origin to multiple destinations sequentially.

    Args:
        origin:       (latitude, longitude)
        destinations: list of (latitude, longitude) tuples
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


# ── Internal helpers ───────────────────────────────────────────────────────────

def _decode_polyline_to_geojson(encoded: str) -> List[List[float]]:
    """
    Decode a Google-format encoded polyline string into a GeoJSON-compatible
    coordinate array.

    The `polyline` library decodes to [(lat, lng), ...].
    GeoJSON / MapLibre requires [[lng, lat], ...] — so each tuple is reversed.

    Args:
        encoded: Encoded polyline string from Ola Maps API.

    Returns:
        List of [lng, lat] pairs, or [] if the input is empty/invalid.
    """
    if not encoded:
        return []
    try:
        # polyline.decode() → [(lat, lng), ...]
        latlon_pairs: List[Tuple[float, float]] = polyline_codec.decode(encoded)
        # Reverse to [lng, lat] for GeoJSON standard
        return [
            [lng, lat]
            for lat, lng in latlon_pairs
            if math.isfinite(lat) and math.isfinite(lng)
        ]
    except Exception as exc:
        logger.error(f"[OlaMaps] Polyline decode failed: {exc}")
        return []


def _normalize_name(name: str) -> str:
    """Strip extra whitespace and title-case a place name."""
    if not name:
        return "Unnamed"
    return " ".join(name.strip().split()).title()


def _estimate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str,
) -> Dict[str, Any]:
    """
    Haversine straight-line distance estimation used when the Ola Maps API is
    unavailable or unconfigured.

    Returns the same contract as `get_route` so callers need no special handling.
    Geometry coordinates are [lng, lat] to match the GeoJSON / MapLibre standard.
    """
    R = 6371.0  # Earth mean radius in km

    lat1 = math.radians(origin[0])
    lon1 = math.radians(origin[1])
    lat2 = math.radians(destination[0])
    lon2 = math.radians(destination[1])

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    )
    dist_km = R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    speed_kmh = _FALLBACK_SPEEDS.get(mode, 35.0)
    duration_min = round((dist_km / speed_kmh) * 60.0, 1)

    return {
        "distance_km":  round(dist_km, 2),
        "duration_min": duration_min,
        "mode":         mode,
        "geometry": {
            "type": "LineString",
            # Two-point straight line — [lng, lat] order for GeoJSON/MapLibre
            "coordinates": [
                [origin[1],      origin[0]],
                [destination[1], destination[0]],
            ],
        },
        "estimated": True,
    }


# ── City-specific mock fallback (offline / API key absent) ────────────────────

def mock_amenities(lat: float, lng: float, radius_m: int = 2000) -> List[Dict[str, Any]]:
    """
    Deterministic city-aware mock POI data for offline development.
    Seeded by coordinates so results are stable per property location.
    """
    import math as _math
    import random

    city = "default"
    if 12.8 <= lat <= 13.1 and 77.5 <= lng <= 77.8:
        city = "bengaluru"
    elif 18.9 <= lat <= 19.3 and 72.7 <= lng <= 73.0:
        city = "mumbai"

    random.seed(int(lat * 1000 + lng * 1000))

    city_data: Dict[str, List[str]] = {
        "bengaluru": {
            "metro":       ["Indiranagar Metro", "Koramangala Metro", "Halasuru Metro"],
            "bus":         ["HSR Layout Bus Stop", "100 Feet Rd Bus Stop"],
            "hospital":    ["Manipal Hospital", "St. John's Medical", "Columbia Asia"],
            "pharmacy":    ["Apollo Pharmacy", "MedPlus", "Trust Pharmacy"],
            "grocery":     ["More Supermarket", "Reliance Fresh", "D-Mart"],
            "park":        ["Koramangala 3rd Block Park", "Cubbon Park"],
            "gym":         ["Cult.fit", "Gold's Gym", "Snap Fitness"],
            "restaurant":  ["Toit Brewpub", "Truffles", "Absolute Barbecues"],
            "cafe":        ["Third Wave Coffee", "Blue Tokai", "Starbucks"],
            "office":      ["Manyata Tech Park", "EcoSpace", "Bagmane Tech Park"],
            "company":     ["Infosys", "Wipro", "TCS"],
            "mall":        ["Nexus Mall", "Phoenix Marketcity", "Garuda Mall"],
            "atm":         ["HDFC ATM", "ICICI ATM", "SBI ATM"],
            "bank":        ["HDFC Bank", "ICICI Bank", "SBI"],
            "school":      ["Bishop Cotton", "National Public School"],
            "college":     ["Christ University", "BMS College"],
            "clinic":      ["Narayana Clinic", "Cloudnine Clinic"],
            "bus_stop":    ["Sony World Signal", "Domlur"],
            "bus_station": ["Koramangala TTMC"],
            "bus_depot":   ["HSR Bus Depot"],
            "supermarket": ["More Megastore", "Reliance Smart"],
            "playground":  ["HSR Sector 2 Playground"],
            "fuel":        ["Indian Oil", "BPCL Pump"],
            "tech_park":   ["RMZ Ecospace", "Bagmane Constellation"],
            "coworking":   ["WeWork Koramangala", "91springboard HSR"],
            "university":  ["IIM Bangalore", "NIMHANS"],
        },
        "mumbai": {
            "metro":       ["Bandra Metro", "Andheri Metro"],
            "bus":         ["Carter Road Bus Stop", "Linking Road Bus Stop"],
            "hospital":    ["Lilavati Hospital", "Holy Family Hospital"],
            "pharmacy":    ["Noble Chemists", "Apollo Pharmacy"],
            "grocery":     ["Nature's Basket", "Reliance Smart"],
            "park":        ["Jogger's Park Bandra", "Shivaji Park"],
            "gym":         ["Gold's Gym Bandra", "Talwalkars"],
            "restaurant":  ["Olive Bar & Kitchen", "The Daily Bar"],
            "cafe":        ["Blue Tokai Bandra", "Subko Coffee"],
            "office":      ["Naman Centre BKC", "One BKC"],
            "company":     ["Reliance Industries BKC", "ICICI Bank HQ"],
            "mall":        ["Phoenix Palladium", "Inorbit Mall"],
            "atm":         ["HDFC ATM BKC", "SBI ATM Bandra"],
            "bank":        ["HDFC Bank Bandra", "ICICI Bank BKC"],
            "school":      ["Dhirubhai Ambani School", "St. Stanislaus"],
            "college":     ["St. Xavier's College", "NMIMS"],
            "clinic":      ["Apollo Clinic Bandra", "Hinduja Clinic"],
            "bus_stop":    ["Otters Club", "Carter Road"],
            "bus_station": ["Bandra Bus Station"],
            "bus_depot":   ["Bandra Bus Depot"],
            "supermarket": ["Foodhall Bandra", "Star Bazaar"],
            "playground":  ["Patwardhan Park Playground"],
            "fuel":        ["Indian Oil Bandra", "HPCL BKC"],
            "tech_park":   ["Nesco IT Park", "Millennium Business Park"],
            "coworking":   ["WeWork BKC", "The Hive Bandra"],
            "university":  ["University of Mumbai", "TISS"],
        },
        "default": {
            "metro":       ["Central Metro", "City Center Metro"],
            "bus":         ["Main Road Bus Stop", "Market Bus Stop"],
            "hospital":    ["City General Hospital", "National Care Hospital"],
            "pharmacy":    ["Apollo Pharmacy", "MedPlus"],
            "grocery":     ["Fresh Mart", "Daily Needs Store"],
            "park":        ["Green Valley Park", "Central Town Park"],
            "gym":         ["FitLife Gym", "PowerHouse Gym"],
            "restaurant":  ["Spice Garden", "Royal Dine"],
            "cafe":        ["Central Cafe", "The Coffee House"],
            "office":      ["Commercial Tech Park", "Business Plaza"],
            "company":     ["MNC Headquarters", "Software Solutions"],
            "mall":        ["City Centre Mall", "Grand Plaza Mall"],
            "atm":         ["National Bank ATM", "Central Bank ATM"],
            "bank":        ["National Trust Bank", "Central Bank"],
            "school":      ["City Public School", "National Academy"],
            "college":     ["City College", "Tech Institute"],
            "clinic":      ["Specialty Clinic", "Primary Health Clinic"],
            "bus_stop":    ["Main Gate Bus Stop", "Cross Road Bus Stop"],
            "bus_station": ["Central Bus Station"],
            "bus_depot":   ["Central Bus Depot"],
            "supermarket": ["Metro Supermarket", "Big Bazaar"],
            "playground":  ["Community Playground"],
            "fuel":        ["Indian Oil Pump", "BPCL Station"],
            "tech_park":   ["Technopark Phase 1", "Cyber City"],
            "coworking":   ["WeWork Hub", "ShareSpace"],
            "university":  ["State University", "Engineering College"],
        },
    }

    names_map = city_data.get(city, city_data["default"])
    results: List[Dict[str, Any]] = []

    for category, name_list in names_map.items():
        name = random.choice(name_list)
        angle = random.uniform(0, 2 * _math.pi)
        dist = random.randint(150, min(radius_m, 2500))
        offset = dist / 111000.0

        results.append({
            "osm_id":      f"mock_{category}_{random.randint(100000, 999999)}",
            "name":        name,
            "category":    category,
            "subcategory": None,
            "lat":         lat + offset * _math.cos(angle),
            "lng":         lng + offset * _math.sin(angle),
            "tags":        {},
        })

    return results
