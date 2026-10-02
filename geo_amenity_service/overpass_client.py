"""
Overpass API Client for amenity discovery via OpenStreetMap.
Supports dynamic radius-based queries for schools, hospitals, metro stations, etc.
"""
import httpx
import logging
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("overpass_client")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# OSM tag mappings per amenity category
CATEGORY_TAGS = {
    "school": '[amenity=school]',
    "college": '[amenity=university]',
    "university": '[amenity=university]',
    "hospital": '[amenity=hospital]',
    "clinic": '[amenity=clinic]',
    "pharmacy": '[amenity=pharmacy]',
    "metro": '[station=subway]',
    "bus": '[highway=bus_stop]',
    "bus_stop": '[highway=bus_stop]',
    "bus_station": '[amenity=bus_station]',
    "bus_depot": '[amenity=bus_station]',
    "grocery": '[shop=supermarket]',
    "supermarket": '[shop=supermarket]',
    "park": '[leisure=park]',
    "playground": '[leisure=playground]',
    "gym": '[leisure=fitness_centre]',
    "fuel": '[amenity=fuel]',
    "restaurant": '[amenity=restaurant]',
    "cafe": '[amenity=cafe]',
    "office": '[building=commercial]',
    "company": '[office=company]',
    "tech_park": '[office=it]',
    "coworking": '[amenity=coworking_space]',
    "mall": '[shop=mall]',
    "atm": '[amenity=atm]',
    "bank": '[amenity=bank]',
}


# Categories that warrant a larger default search radius
LARGE_RADIUS_CATEGORIES: frozenset = frozenset({"hospital", "office", "company", "tech_park", "coworking"})

# Per-category default radii (metres)
CATEGORY_DEFAULT_RADIUS: Dict[str, int] = {
    category: (5000 if category in LARGE_RADIUS_CATEGORIES else 2000)
    for category in CATEGORY_TAGS
}


async def fetch_amenities_by_category_radius(
    lat: float,
    lng: float,
    categories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch amenities using per-category radius rules:
    - hospital / office family  → 5 000 m
    - all others                → 2 000 m with auto-expansion fallback to 5 000 m
    Results from all categories are merged and returned together.
    """
    if categories is None:
        categories = list(CATEGORY_TAGS.keys())

    all_results: List[Dict[str, Any]] = []
    seen_ids: set = set()

    for category in categories:
        tag = CATEGORY_TAGS.get(category)
        if not tag:
            continue

        primary_radius = CATEGORY_DEFAULT_RADIUS.get(category, 2000)
        radii_to_try: List[int] = (
            [primary_radius]                  # large-radius categories: single pass
            if primary_radius >= 5000
            else [primary_radius, 5000]       # standard categories: try 2 km, expand to 5 km
        )

        category_results: List[Dict[str, Any]] = []

        for radius_m in radii_to_try:
            batch = await _fetch_single_category(lat, lng, category, tag, radius_m, seen_ids)
            if batch:
                category_results = batch
                break  # found results at this radius — no need to expand further

        all_results.extend(category_results)

    return all_results


async def _fetch_single_category(
    lat: float,
    lng: float,
    category: str,
    tag: str,
    radius_m: int,
    seen_ids: set,
) -> List[Dict[str, Any]]:
    """
    Execute one Overpass query for a single category at a given radius.
    Updates `seen_ids` in-place to deduplicate across callers.
    Returns the list of new amenity dicts found (may be empty).
    """
    query = f"""
    [out:json][timeout:10];
    (
      node{tag}(around:{radius_m},{lat},{lng});
      way{tag}(around:{radius_m},{lat},{lng});
    );
    out center tags;
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://rentora.in",
    }

    results: List[Dict[str, Any]] = []
    try:
        timeout_cfg = httpx.Timeout(10.0, connect=1.5)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query}, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Overpass API returned {resp.status_code} for category {category} @ {radius_m}m")
                return results

            data = resp.json()
            for element in data.get("elements", []):
                osm_id = element.get("id")
                if osm_id in seen_ids:
                    continue
                seen_ids.add(osm_id)

                # Nodes carry lat/lon directly; ways carry a computed centre
                el_lat: Optional[float] = element.get("lat") or element.get("center", {}).get("lat")
                el_lng: Optional[float] = element.get("lon") or element.get("center", {}).get("lon")

                if el_lat is None or el_lng is None:
                    continue

                tags = element.get("tags", {})
                name = tags.get("name", tags.get("operator", f"{category.title()} (Unnamed)"))

                results.append({
                    "osm_id": osm_id,
                    "name": _normalize_name(name),
                    "category": category,
                    "subcategory": tags.get("cuisine") or tags.get("shop") or None,
                    # Overpass returns lat (latitude) and lon (longitude) — stored as-is
                    "lat": float(el_lat),
                    "lng": float(el_lng),
                    "tags": tags,
                })

    except httpx.RequestError as req_err:
        logger.error(f"Overpass network request failed for {category}: {req_err}")
        raise req_err
    except Exception as e:
        logger.error(f"Overpass query failed for {category}: {e}")

    return results


async def fetch_amenities(
    lat: float,
    lng: float,
    categories: Optional[List[str]] = None,
    radius_m: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Query the Overpass API for amenities around a coordinate point.
    Returns normalized amenity list with deduplication.

    When an explicit `radius_m` is provided (legacy callers) every category is
    queried at that single radius.  Prefer `fetch_amenities_by_category_radius`
    for production use so that per-category radii and auto-expansion apply.
    """
    if categories is None:
        categories = list(CATEGORY_TAGS.keys())

    results: List[Dict[str, Any]] = []
    seen_ids: set = set()

    for category in categories:
        tag = CATEGORY_TAGS.get(category)
        if not tag:
            continue
        batch = await _fetch_single_category(lat, lng, category, tag, radius_m, seen_ids)
        results.extend(batch)

    return results


def _normalize_name(name: str) -> str:
    """Normalize amenity name: strip extra whitespace, title-case."""
    if not name:
        return "Unnamed"
    return " ".join(name.strip().split()).title()


# Mock fallback for development/offline usage
def mock_amenities(lat: float, lng: float, radius_m: int = 2000) -> List[Dict[str, Any]]:
    """Returns deterministic mock amenity data for offline development mapped to city context."""
    import math
    import random
    
    # Determine city context based on lat/lng range
    city = "default"
    if 12.8 <= lat <= 13.1 and 77.5 <= lng <= 77.8:
        city = "bengaluru"
    elif 18.9 <= lat <= 19.3 and 72.7 <= lng <= 73.0:
        city = "mumbai"

    # Seed with coords so it is deterministic for each property
    random.seed(int(lat * 1000 + lng * 1000))

    # Rich city-specific mock lists
    if city == "bengaluru":
        local_names = {
            "metro": ["Indiranagar Metro Station", "Koramangala Metro Station", "Halasuru Metro Station", "Trinity Metro Station"],
            "bus": ["HSR Layout Bus Stop", "Indiranagar 100 Feet Rd Bus Stop", "Sony World Signal Bus Stop"],
            "bus_depot": ["HSR Bus Depot", "Koramangala TTMC", "Domlur Bus Depot"],
            "bus_station": ["Koramangala TTMC", "Domlur Bus Station"],
            "bus_stop": ["HSR Layout Bus Stop", "Sony World Signal Bus Stop"],
            "hospital": ["Manipal Hospital", "St. John's Medical College Hospital", "Columbia Asia Hospital"],
            "clinic": ["Narayana Health Clinic", "Cloudnine Clinic"],
            "pharmacy": ["Apollo Pharmacy", "MedPlus Pharmacy", "Trust Pharmacy"],
            "grocery": ["More Supermarket", "Reliance Fresh", "D-Mart Ready"],
            "supermarket": ["More Megastore", "Reliance Smart", "Spar Hypermarket"],
            "park": ["Koramangala 3rd Block Park", "HSR Sector 3 Park", "Cubbon Park"],
            "playground": ["HSR Sector 2 Playground", "Indiranagar Defence Colony Playground"],
            "gym": ["Cult.fit Gym", "Gold's Gym", "Snap Fitness"],
            "restaurant": ["Toit Brewpub", "Truffles Cafe", "Chutney Chang", "Absolute Barbecues"],
            "cafe": ["Third Wave Coffee Roasters", "Blue Tokai Coffee", "Starbucks"],
            "office": ["Manyata Tech Park", "EcoSpace IT Park", "Bagmane Tech Park"],
            "company": ["Infosys Campus", "Wipro Technologies", "TCS Office"],
            "tech_park": ["Bagmane Constellation Business Park", "RMZ Ecospace"],
            "coworking": ["WeWork Koramangala", "91springboard HSR", "Awfis Space"],
            "mall": ["Nexus Mall Koramangala", "Phoenix Marketcity", "Garuda Mall"],
            "atm": ["HDFC Bank ATM", "ICICI Bank ATM", "SBI ATM"],
            "bank": ["HDFC Bank", "ICICI Bank", "State Bank of India"]
        }
    elif city == "mumbai":
        local_names = {
            "metro": ["Bandra Metro Station", "Versova Metro Station", "Andheri Metro Station"],
            "bus": ["Bandra West Bus Stop", "Carter Road Bus Stop", "Linking Road Bus Stop"],
            "bus_depot": ["Bandra Bus Depot", "Santacruz Bus Depot", "Kurla Bus Depot"],
            "bus_station": ["Bandra Terminus Bus Station", "Andheri West Station Bus Stop"],
            "bus_stop": ["Carter Road Promenade Bus Stop", "Otters Club Bus Stop"],
            "hospital": ["Lilavati Hospital", "Bhabha Hospital", "Holy Family Hospital"],
            "clinic": ["Apollo Clinic Bandra", "Hinduja Healthcare Clinic"],
            "pharmacy": ["Noble Chemists", "Apollo Pharmacy", "Wellness Forever"],
            "grocery": ["Nature's Basket Bandra", "Reliance Smart", "Society Supermarket"],
            "supermarket": ["Foodhall Bandra", "Star Bazaar", "Reliance Fresh"],
            "park": ["Jogger's Park Bandra", "Carter Road Children's Park", "Shivaji Park"],
            "playground": ["Patwardhan Park Playground", "Bandra YMCA Ground"],
            "gym": ["Gold's Gym Bandra", "Nitro Fitness", "Talwalkars Gym"],
            "restaurant": ["Olive Bar & Kitchen", "Global Fusion", "The Daily Bar & Kitchen"],
            "cafe": ["Blue Tokai Bandra", "Starbucks Carter Road", "Subko Coffee Roasters"],
            "office": ["Naman Centre BKC", "Maker Maxity BKC", "One BKC"],
            "company": ["Reliance Industries BKC", "ICICI Bank HQ", "NSE Office BKC"],
            "tech_park": ["Nesco IT Park", "Millennium Business Park"],
            "coworking": ["WeWork BKC", "The Hive Bandra", "Regus BKC"],
            "mall": ["Phoenix Palladium", "Phoenix Marketcity Kurla", "Inorbit Mall"],
            "atm": ["HDFC Bank ATM BKC", "ICICI Bank ATM Carter Rd", "SBI ATM Bandra West"],
            "bank": ["HDFC Bank Bandra West", "ICICI Bank BKC", "State Bank of India"]
        }
    else:
        local_names = {
            "metro": ["Central Metro Station", "City Center Metro Station"],
            "bus": ["Main Road Bus Stop", "Market Road Bus Stop"],
            "bus_depot": ["Central Bus Depot", "Intercity Bus Terminal"],
            "bus_station": ["Central Bus Station", "Sub-urban Bus Stand"],
            "bus_stop": ["Main Gate Bus Stop", "Cross Road Bus Stop"],
            "hospital": ["City General Hospital", "National Care Hospital"],
            "clinic": ["Specialty Clinic", "Primary Health Clinic"],
            "pharmacy": ["Apollo Pharmacy", "MedPlus Pharmacy"],
            "grocery": ["Fresh Mart Supermarket", "Daily Needs Store"],
            "supermarket": ["Metro Supermarket", "Big Bazaar"],
            "park": ["Green Valley Park", "Central Town Park"],
            "playground": ["Community Playground", "Children's Play Park"],
            "gym": ["FitLife Gym", "PowerHouse Gym"],
            "restaurant": ["Spice Garden", "Royal Dine"],
            "cafe": ["Central Cafe", "The Coffee House"],
            "office": ["Commercial Tech Park", "Business Plaza"],
            "company": ["MNC Headquarters", "Software Solutions Office"],
            "tech_park": ["Technopark Phase 1", "Cyber City IT Park"],
            "coworking": ["WeWork Hub", "ShareSpace Coworking"],
            "mall": ["City Centre Mall", "Grand Plaza Mall"],
            "atm": ["National Bank ATM", "Central Bank ATM"],
            "bank": ["National Trust Bank", "Central Bank"]
        }

    results = []
    # Generate 1 POI per category from local name arrays
    for category, names in local_names.items():
        name = random.choice(names)
        angle = random.uniform(0, 2 * math.pi)
        # Random distance within 200m to 2500m
        dist = random.randint(150, min(radius_m, 2500))
        offset = dist / 111000.0
        
        results.append({
            "osm_id": random.randint(100000, 999999),
            "name": name,
            "category": category,
            "subcategory": None,
            "lat": lat + offset * math.cos(angle),
            "lng": lng + offset * math.sin(angle),
            "tags": {},
        })
        
    return results
