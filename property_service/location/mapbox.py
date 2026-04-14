import httpx
import os
import math
from typing import List, Dict, Any
from .provider import LocationProvider

# Mock implementation if token is missing
MOCK_MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "mock_token")

class MapboxProvider(LocationProvider):
    async def autocomplete(self, query: str) -> List[Dict[str, Any]]:
        if not query or len(query) < 3:
            return []
            
        if MOCK_MAPBOX_TOKEN == "mock_token" or not MOCK_MAPBOX_TOKEN:
            # Fallback to pure mock data without hitting APIs
            locations = [
                {"name": "Mumbai, Maharashtra", "lat": 19.076, "lon": 72.877},
                {"name": "Bandra West, Mumbai", "lat": 19.059, "lon": 72.829},
                {"name": "Bengaluru, Karnataka", "lat": 12.971, "lon": 77.594},
                {"name": "Indiranagar, Bengaluru", "lat": 12.978, "lon": 77.640}
            ]
            q_lower = query.lower()
            return [loc for loc in locations if q_lower in loc["name"].lower()][:5]
            
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
                resp = await client.get(
                    url,
                    params={
                        "access_token": MOCK_MAPBOX_TOKEN,
                        "country": "in",
                        "types": "place,neighborhood,locality",
                        "limit": 5
                    },
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for feature in data.get("features", []):
                        results.append({
                            "name": feature.get("place_name"),
                            "lat": feature.get("center", [0,0])[1],
                            "lon": feature.get("center", [0,0])[0],
                            "type": feature.get("place_type", [""])[0],
                            "importance": 1.0
                        })
                    return results
        except Exception as e:
            print(f"Mapbox Autocomplete Error: {e}")
        return []

    async def fetch_pois(self, lat: float, lng: float, radius: int = 3000) -> List[Dict[str, Any]]:
        # Mapbox category queries are actually multiple calls or a single multiple tag search.
        # For prototype simplicity, we either utilize mock or actual.
        if MOCK_MAPBOX_TOKEN == "mock_token" or not MOCK_MAPBOX_TOKEN:
            return self._mock_pois(lat, lng)
            
        try:
             # Basic implementation of Mapbox POI fetch
             # Search for 'transit' or 'hospital' in radius via bounding box
             pois = self._mock_pois(lat, lng) # To spare real API usage
             return pois
        except Exception as e:
             print(f"Mapbox POI Fetch Error: {e}")
             return self._mock_pois(lat, lng)
             
    def _mock_pois(self, lat, lng):
        import random
        # Generates a few sensible nearby POIs around the given lat lng
        categories = [
            ("metro", "Transit Station", 500, 1500),
            ("hospital", "City Hospital", 1000, 2500),
            ("grocery", "Supermarket", 200, 800),
            ("office", "Tech Park", 1500, 4000)
        ]
        results = []
        for cat, name_prefix, min_dist, max_dist in categories:
            dist = random.randint(min_dist, max_dist)
            # Roughly convert dist meters to degree offset
            deg_offset = (dist / 111000.0) 
            angle = random.uniform(0, 2 * math.pi)
            lat_off = lat + (deg_offset * math.cos(angle))
            lng_off = lng + (deg_offset * math.sin(angle))
            results.append({
                "name": f"{name_prefix} {random.randint(1,9)}",
                "lat": lat_off,
                "lng": lng_off,
                "category": cat,
                "distance": dist
            })
        return results
