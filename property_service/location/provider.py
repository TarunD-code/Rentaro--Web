from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class LocationProvider(ABC):
    @abstractmethod
    async def autocomplete(self, query: str) -> List[Dict[str, Any]]:
        """
        Returns a list of search suggestions.
        Format: [{"name": str, "lat": float, "lon": float, "type": str, "importance": float}]
        """
        pass

    @abstractmethod
    async def geocode(self, address: str) -> Tuple[float, float]:
        """
        Returns lat, lng for an address
        """
        pass

    @abstractmethod
    async def fetch_pois(self, lat: float, lng: float, radius: int = 3000) -> List[Dict[str, Any]]:
        """
        Returns Points Of Interest around a coordinate.
        Format: [{"name": str, "lat": float, "lng": float, "category": str, "distance": float}]
        Category enum approx: 'metro', 'hospital', 'grocery', 'office', 'school'
        """
        pass

    @abstractmethod
    async def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float], mode: str = "transit") -> Dict[str, Any]:
        """
        Returns routing info between two points.
        Format: {"distance": float, "duration": float, "mode": str}
        """
        pass
