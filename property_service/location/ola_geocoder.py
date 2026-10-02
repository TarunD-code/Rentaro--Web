"""
Ola Maps Geocoder — Bengaluru-biased address resolution
=========================================================
Provides a single async function `geocode_address` that converts a freeform
Indian address string into (lat, lng) using the Ola Maps Geocode API.

The bounding-box bias keeps results anchored to Greater Bengaluru so that
queries like "HSR Layout, 560102" don't resolve to the wrong city.

Bengaluru bounding box (approx BBMP + adjoining areas):
    SW: (12.7342, 77.3791)
    NE: (13.1739, 77.8280)

API reference:
    GET https://api.olamaps.io/places/v1/geocode
    Params: address, bounds, api_key, language
    Response: { geocodingResults: [{ geometry: { location: { lat, lng } } }] }
"""

import os
import logging
from typing import Optional, Tuple

import httpx

logger = logging.getLogger("ola_geocoder")

_OLA_MAPS_API_KEY: str = os.environ.get("OLA_MAPS_API_KEY", "")
_GEOCODE_URL = "https://api.olamaps.io/places/v1/geocode"

# Bengaluru bounding box — "SW_lat,SW_lng|NE_lat,NE_lng"
_BLR_BOUNDS = "12.7342,77.3791|13.1739,77.8280"

# Hard fallback coordinates: Bengaluru city centre (MG Road / Trinity Circle)
# Used only when the API is unconfigured AND no coordinates exist yet.
_BLR_FALLBACK_LAT = 12.9716
_BLR_FALLBACK_LNG = 77.5946


def _build_query(address: str, area: str = "", city: str = "Bengaluru", pincode: str = "") -> str:
    """
    Normalise address fields into a single geocoding query string.
    Follows the pattern: {area}, {city}, Karnataka, {pincode}, India
    """
    parts = [p.strip() for p in [address, area, city, "Karnataka", pincode, "India"] if p and p.strip()]
    # Deduplicate consecutive duplicates (e.g. city appears in both address and city field)
    deduped = [parts[0]] + [b for a, b in zip(parts, parts[1:]) if a.lower() != b.lower()]
    return ", ".join(deduped)


async def geocode_address(
    address: str,
    area: str = "",
    city: str = "Bengaluru",
    pincode: str = "",
) -> Tuple[Optional[float], Optional[float]]:
    """
    Resolve an address to (lat, lng) using the Ola Maps Geocode API.

    Returns (lat, lng) on success, (None, None) on failure.
    Never raises — callers should check for None and decide whether to
    use the fallback or reject the request.

    Args:
        address:  Street / building / society name.
        area:     Locality / area name (e.g. "Koramangala 5th Block").
        city:     City (defaults to "Bengaluru").
        pincode:  6-digit PIN code.
    """
    if not _OLA_MAPS_API_KEY:
        logger.warning(
            "[OlaGeocode] OLA_MAPS_API_KEY not set — cannot geocode. "
            "Property will be created without coordinates."
        )
        return None, None

    query = _build_query(address, area, city, pincode)
    logger.info(f"[OlaGeocode] Resolving: '{query}'")

    params = {
        "address":  query,
        "bounds":   _BLR_BOUNDS,
        "language": "en",
        "api_key":  _OLA_MAPS_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            resp = await client.get(_GEOCODE_URL, params=params)

        if resp.status_code != 200:
            logger.warning(
                f"[OlaGeocode] HTTP {resp.status_code} for '{query}': {resp.text[:200]}"
            )
            return None, None

        data = resp.json()

        # Response shape: { "geocodingResults": [ { "geometry": { "location": { "lat": N, "lng": N } } } ] }
        results = data.get("geocodingResults") or data.get("results") or []
        if not results:
            logger.warning(f"[OlaGeocode] No results for '{query}'")
            return None, None

        # Take the first (highest-confidence) result
        location = results[0].get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng") or location.get("lon")

        if lat is None or lng is None:
            logger.warning(f"[OlaGeocode] Result missing coordinates for '{query}': {results[0]}")
            return None, None

        logger.info(f"[OlaGeocode] Resolved '{query}' → ({lat:.5f}, {lng:.5f})")
        return float(lat), float(lng)

    except httpx.RequestError as exc:
        logger.error(f"[OlaGeocode] Network error for '{query}': {exc}")
        return None, None
    except Exception as exc:
        logger.error(f"[OlaGeocode] Unexpected error for '{query}': {exc}")
        return None, None
