import os
from .provider import LocationProvider
from .maptiler import MapTilerProvider
from .google import GoogleProvider

def get_provider() -> LocationProvider:
    provider_name = os.environ.get("MAP_PROVIDER", "maptiler").lower()
    
    if provider_name == "google":
        return GoogleProvider()
    
    # Default to maptiler (Phase 1 prototype)
    return MapTilerProvider()

provider = get_provider()
