import httpx
import os
import math
from typing import List, Dict, Any, Tuple
from .provider import LocationProvider

MAPTILER_KEY = os.environ.get("MAPTILER_KEY", "VGr2EA4T8DcPNjZSXJos")

class MapTilerProvider(LocationProvider):
    async def autocomplete(self, query: str) -> List[Dict[str, Any]]:
        if not query or len(query) < 3:
            return []
            
        if MAPTILER_KEY == "mock_key":
            locations = [
                {"name": "Electronic City Phase 1, Bengaluru", "lat": 12.8452, "lon": 77.6602},
                {"name": "Bandra West, Mumbai", "lat": 19.0596, "lon": 72.8295},
                {"name": "Whitefield, Bengaluru", "lat": 12.9698, "lon": 77.7499}
            ]
            q_lower = query.lower()
            return [loc for loc in locations if q_lower in loc["name"].lower()][:5]
            
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.maptiler.com/geocoding/{query}.json"
                resp = await client.get(
                    url,
                    params={
                        "key": MAPTILER_KEY,
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
            print(f"MapTiler Autocomplete Error: {e}")
        return []

    async def geocode(self, address: str) -> Tuple[float, float]:
        if MAPTILER_KEY == "mock_key":
            return (12.8452, 77.6602) # Electronic city default
            
        try:
             async with httpx.AsyncClient() as client:
                url = f"https://api.maptiler.com/geocoding/{address}.json"
                resp = await client.get(url, params={"key": MAPTILER_KEY, "limit": 1})
                if resp.status_code == 200:
                   data = resp.json()
                   if data.get("features"):
                       center = data["features"][0].get("center")
                       return (center[1], center[0])
        except Exception as e:
            print(f"MapTiler Geocode Error: {e}")
        return (0.0, 0.0)

    async def fetch_pois(self, lat: float, lng: float, radius: int = 3000) -> List[Dict[str, Any]]:
        if MAPTILER_KEY == "mock_key":
            return self._mock_pois(lat, lng)
            
        # In real life, MapTiler Places API / Categories
        # E.g. https://api.maptiler.com/v1/places/search/...
        # For prototype, we're returning mock payload structure to emulate fetched data
        return self._mock_pois(lat, lng)

    async def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float], mode: str = "transit") -> Dict[str, Any]:
        """ Calculate routing from start to end  """
        if MAPTILER_KEY == "mock_key":
            # Just rough euclidean for mock
            lat_diff = end_coords[0] - start_coords[0]
            lng_diff = end_coords[1] - start_coords[1]
            dist_km = math.sqrt(lat_diff*lat_diff + lng_diff*lng_diff) * 111.0 # approx
            return {
                "distance": round(dist_km, 2),
                "duration": round(dist_km * 12, 1), # 12 mins per km roughly
                "mode": mode
            }
            
        try:
            async with httpx.AsyncClient() as client:
               # MapTiler Routing API: driving, pedestrian, transit, bicycle
               url = "https://api.maptiler.com/routes/"
               resp = await client.get(f"{url}?route={start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}&key={MAPTILER_KEY}")
               # Simplify parsing for prototype
               return {
                   "distance": 2.5,
                   "duration": 15.0,
                   "mode": mode
               }
        except Exception as e:
            print(f"MapTiler Routing Error: {e}")
            return {"distance": 0, "duration": 0, "mode": mode}

             
    def _mock_pois(self, lat, lng):
        import random
        categories = [
            ("metro", "Metro Station Phase 1", 500, 1500),
            ("hospital", "City General Hospital", 1000, 2500),
            ("grocery", "Fresh Supermarket", 200, 800),
            ("office", "Tech Park Sez", 1500, 4000)
        ]
        results = []
        for cat, name_prefix, min_dist, max_dist in categories:
            dist = random.randint(min_dist, max_dist)
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
