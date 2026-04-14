from .provider import LocationProvider
from typing import List, Dict, Any, Tuple

class GoogleProvider(LocationProvider):
    async def autocomplete(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Google Maps Phase 2 is not yet active. Check MAP_MIGRATION.md")

    async def geocode(self, address: str) -> Tuple[float, float]:
        raise NotImplementedError("Google Maps Phase 2 is not yet active. Check MAP_MIGRATION.md")

    async def fetch_pois(self, lat: float, lng: float, radius: int = 3000) -> List[Dict[str, Any]]:
        raise NotImplementedError("Google Maps Phase 2 is not yet active. Check MAP_MIGRATION.md")

    async def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float], mode: str = "transit") -> Dict[str, Any]:
         raise NotImplementedError("Google Maps Phase 2 is not yet active. Check MAP_MIGRATION.md")
