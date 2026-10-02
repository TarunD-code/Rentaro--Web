"""
Rentora Geo Amenity Service — Port 8014
Provides spatial amenity discovery, commute intelligence, and locality scoring.

Routing engine:  Ola Maps Directions API  (replaces ORS / OSRM)
POI discovery:   Ola Maps Nearby Search   (replaces Overpass / OSM)
"""
import os
import sys
import json
import logging
from typing import Optional, List, Dict

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .database import get_db, engine
from . import ola_maps_client
from . import locality_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geo_amenity_service")

app = FastAPI(title="Rentora Geo Amenity Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_ensure_schema():
    """
    Idempotently create the geo_amenity schema and amenity_points table,
    and migrate osm_id from BIGINT to TEXT if the column was created with
    the old integer type. This eliminates the manual initialize_postgis.py
    prerequisite and prevents startup mapping mismatches.
    """
    from sqlalchemy import text as sql_text

    DDL = [
        "CREATE EXTENSION IF NOT EXISTS postgis;",
        "CREATE SCHEMA IF NOT EXISTS geo_amenity;",
        """
        CREATE TABLE IF NOT EXISTS geo_amenity.amenity_points (
            id         SERIAL PRIMARY KEY,
            osm_id     TEXT,
            name       VARCHAR(512) NOT NULL,
            category   VARCHAR(64)  NOT NULL,
            subcategory VARCHAR(128),
            lat        DOUBLE PRECISION NOT NULL,
            lng        DOUBLE PRECISION NOT NULL,
            geom       geometry(Point, 4326),
            source     VARCHAR(32) DEFAULT 'ola_maps',
            raw_tags   JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(osm_id, category)
        );
        """,
        # Migrate BIGINT → TEXT if the table was created with the old schema
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'geo_amenity'
                  AND table_name   = 'amenity_points'
                  AND column_name  = 'osm_id'
                  AND data_type    = 'bigint'
            ) THEN
                ALTER TABLE geo_amenity.amenity_points
                    ALTER COLUMN osm_id TYPE TEXT USING osm_id::TEXT;
            END IF;
        END $$;
        """,
        "CREATE INDEX IF NOT EXISTS idx_amenity_points_geom     ON geo_amenity.amenity_points USING GIST (geom);",
        "CREATE INDEX IF NOT EXISTS idx_amenity_points_category ON geo_amenity.amenity_points (category);",
    ]

    try:
        with engine.connect() as conn:
            for stmt in DDL:
                try:
                    conn.execute(sql_text(stmt))
                    conn.commit()
                except Exception as ddl_exc:
                    logger.warning(f"[startup_ensure_schema] DDL warning (non-fatal): {ddl_exc}")
                    conn.rollback()
        logger.info("[startup_ensure_schema] geo_amenity schema ready ✓")
    except Exception as exc:
        logger.error(f"[startup_ensure_schema] Failed — service will run but persistence may fail: {exc}")


@app.get("/health")
def health_check():
    return {
        "status":  "healthy",
        "service": "geo_amenity_service",
        "engine":  "ola_maps",
    }


# ─── AMENITY DISCOVERY ───────────────────────────────────────────────────────

@app.get("/amenities/nearby")
async def get_nearby_amenities(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(
        2000,
        description=(
            "Search radius in metres. Ignored when no explicit categories are "
            "provided — smart per-category radii apply in that case."
        ),
    ),
    categories: Optional[str] = Query(
        None, description="Comma-separated category names"
    ),
):
    """
    Discover nearby amenities via Ola Maps Places API.

    Smart-radius path (no explicit categories):
      - hospital / office family → 5 000 m
      - all others               → 2 000 m, auto-expands to 5 000 m if empty

    Legacy fixed-radius path (explicit categories + radius):
      - Queries Ola Maps for each requested category at the given radius.
    """
    cat_list: Optional[List[str]] = categories.split(",") if categories else None
    use_smart_radius = cat_list is None

    # ── Cache key ──────────────────────────────────────────────────────────────
    if use_smart_radius:
        cache_key = f"ola_amenities_smart:{lat:.4f}:{lng:.4f}"
    else:
        if radius not in [500, 1000, 2000, 5000]:
            radius = 2000
        cache_key = f"ola_amenities:{lat:.4f}:{lng:.4f}:{radius}"

    try:
        import shared_redis
        cached = shared_redis.get(cache_key)
        if cached:
            logger.info(f"[Amenity Cache HIT] {cache_key}")
            return json.loads(cached)
    except Exception:
        pass

    # ── Fetch amenities ────────────────────────────────────────────────────────
    amenities: List[Dict] = []

    if use_smart_radius:
        try:
            amenities = await ola_maps_client.fetch_amenities_by_category_radius(
                lat, lng
            )
            if not amenities:
                logger.info("[OlaMaps] Smart-radius query returned no results — using mock.")
                amenities = ola_maps_client.mock_amenities(lat, lng, 5000)
        except Exception as exc:
            logger.warning(f"[OlaMaps] Smart-radius fetch failed: {exc} — using mock.")
            amenities = ola_maps_client.mock_amenities(lat, lng, 5000)
    else:
        for category in (cat_list or []):
            try:
                batch = await ola_maps_client.fetch_nearby_amenities(
                    lat, lng, category, radius
                )
                amenities.extend(batch)
            except Exception as exc:
                logger.warning(
                    f"[OlaMaps] fetch_nearby_amenities failed for '{category}': {exc}"
                )

        if not amenities:
            logger.info("[OlaMaps] Fixed-radius query returned no results — using mock.")
            amenities = ola_maps_client.mock_amenities(lat, lng, radius)

    # ── Attach Haversine distances and sort ────────────────────────────────────
    for a in amenities:
        a["distance_m"] = round(
            locality_engine.haversine_distance_m(lat, lng, a["lat"], a["lng"])
        )
    amenities.sort(key=lambda x: x["distance_m"])

    effective_radius = 5000 if use_smart_radius else radius
    result = {
        "amenities": amenities,
        "count":     len(amenities),
        "radius_m":  effective_radius,
    }

    # Cache for 6 hours
    try:
        import shared_redis
        shared_redis.set(cache_key, json.dumps(result), ttl=21600)
    except Exception:
        pass

    # Persist for historical lookups
    try:
        _persist_amenities(amenities)
    except Exception as exc:
        logger.warning(f"Amenity persistence error: {exc}")

    return result


def _persist_amenities(amenities: list):
    """Upsert discovered amenities into geo_amenity.amenity_points."""
    try:
        from sqlalchemy import text as sql_text

        with engine.connect() as conn:
            for a in amenities:
                conn.execute(
                    sql_text("""
                        INSERT INTO geo_amenity.amenity_points
                            (osm_id, name, category, subcategory, lat, lng, geom, raw_tags)
                        VALUES
                            (:osm_id, :name, :category, :subcategory, :lat, :lng,
                             ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :tags)
                        ON CONFLICT (osm_id, category) DO UPDATE SET
                            name        = EXCLUDED.name,
                            lat         = EXCLUDED.lat,
                            lng         = EXCLUDED.lng,
                            geom        = EXCLUDED.geom,
                            updated_at  = NOW()
                    """),
                    {
                        "osm_id":     str(a.get("osm_id", "")),
                        "name":       a["name"],
                        "category":   a["category"],
                        "subcategory": a.get("subcategory"),
                        "lat":        a["lat"],
                        "lng":        a["lng"],
                        "tags":       json.dumps(a.get("tags", {})),
                    },
                )
            conn.commit()
    except Exception as exc:
        logger.warning(f"Amenity persistence error: {exc}")


# ─── LOCALITY SCORING ────────────────────────────────────────────────────────

@app.get("/locality/score")
async def get_locality_score(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = Query(2000),
):
    """Compute the Rentora Smart Locality Score™ for a coordinate."""
    cache_key = f"locality_score:{lat:.4f}:{lng:.4f}:{radius}"
    try:
        import shared_redis
        cached = shared_redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    try:
        amenities = await ola_maps_client.fetch_amenities_by_category_radius(lat, lng)
        if not amenities:
            amenities = ola_maps_client.mock_amenities(lat, lng, radius)
    except Exception:
        amenities = ola_maps_client.mock_amenities(lat, lng, radius)

    category_distances: Dict[str, List[float]] = {}
    for a in amenities:
        dist = locality_engine.haversine_distance_m(lat, lng, a["lat"], a["lng"])
        cat = a["category"]
        category_distances.setdefault(cat, []).append(dist)

    scores = locality_engine.compute_locality_score(category_distances)

    try:
        import shared_redis
        shared_redis.set(cache_key, json.dumps(scores), ttl=43200)
    except Exception:
        pass

    try:
        import shared_event_broker
        shared_event_broker.publish_event(
            "locality_score_updated",
            {"lat": lat, "lng": lng, "scores": scores},
            "geo_amenity_service",
        )
    except Exception:
        pass

    return scores


@app.get("/locality/score/property/{property_id}")
async def get_property_locality_score(
    property_id: int,
    db: Session = Depends(get_db),
):
    """Calculate locality score for a specific property by its database ID."""
    try:
        row = db.execute(
            text("SELECT lat, lng FROM property.properties WHERE id = :pid"),
            {"pid": property_id},
        ).fetchone()

        if not row or row[0] is None or row[1] is None:
            raise HTTPException(
                status_code=404,
                detail="Property not found or missing coordinates",
            )

        return await get_locality_score(lat=row[0], lng=row[1])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ─── COMMUTE INTELLIGENCE ────────────────────────────────────────────────────

@app.get("/commute/route")
async def get_commute_route(
    origin_lat: float = Query(...),
    origin_lng: float = Query(...),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
    mode: str = Query("driving", description="driving, walking, cycling"),
):
    """
    Calculate a traffic-aware commute route using Ola Maps Directions API.
    Returns GeoJSON LineString geometry directly consumable by MapLibre GL.
    """
    if mode not in ("driving", "walking", "cycling"):
        mode = "driving"

    return await ola_maps_client.get_route(
        (origin_lat, origin_lng),
        (dest_lat, dest_lng),
        mode,
    )


@app.get("/commute/matrix")
async def get_commute_matrix(
    origin_lat: float = Query(...),
    origin_lng: float = Query(...),
    dest_coords: str = Query(
        ..., description="Semicolon-separated lat,lng pairs e.g. 12.97,77.59;12.84,77.66"
    ),
    mode: str = Query("driving"),
):
    """Calculate commute times from one origin to multiple destinations."""
    destinations = []
    for pair in dest_coords.split(";"):
        parts = pair.strip().split(",")
        if len(parts) == 2:
            try:
                destinations.append((float(parts[0]), float(parts[1])))
            except ValueError:
                pass

    if not destinations:
        raise HTTPException(status_code=400, detail="No valid destination coordinates")

    matrix = await ola_maps_client.get_commute_matrix(
        (origin_lat, origin_lng),
        destinations,
        mode,
    )
    return {"origin": {"lat": origin_lat, "lng": origin_lng}, "routes": matrix}


@app.get("/commute/score")
async def get_commute_score(
    property_lat: float = Query(...),
    property_lng: float = Query(...),
    office_lat: float = Query(...),
    office_lng: float = Query(...),
):
    """Generate a commute quality score (1–10) between a property and office."""
    route = await ola_maps_client.get_route(
        (property_lat, property_lng),
        (office_lat, office_lng),
        "driving",
    )

    duration = route.get("duration_min", 60.0)

    if duration <= 10:
        score = 10.0
    elif duration <= 20:
        score = 9.0 - ((duration - 10) / 10) * 1.0
    elif duration <= 30:
        score = 8.0 - ((duration - 20) / 10) * 1.5
    elif duration <= 45:
        score = 6.5 - ((duration - 30) / 15) * 2.0
    elif duration <= 60:
        score = 4.5 - ((duration - 45) / 15) * 1.5
    else:
        score = max(1.0, 3.0 - ((duration - 60) / 30) * 2.0)

    return {
        "commute_score": round(score, 1),
        "drive_time_min": duration,
        "distance_km":   route.get("distance_km", 0),
        "rating": (
            "Excellent" if score >= 8 else
            "Good"      if score >= 6 else
            "Fair"      if score >= 4 else
            "Poor"
        ),
    }


# ─── GEO SEARCH ENDPOINTS ────────────────────────────────────────────────────

@app.get("/search/viewport")
def search_by_viewport(
    min_lat: float = Query(...),
    min_lng: float = Query(...),
    max_lat: float = Query(...),
    max_lng: float = Query(...),
    limit: int = Query(100),
    db: Session = Depends(get_db),
):
    """PostGIS viewport bounding-box property search."""
    try:
        rows = db.execute(
            text("""
                SELECT id, title, address, price, property_type, lat, lng,
                       commute_score, is_featured, is_verified, status
                FROM property.properties
                WHERE geom IS NOT NULL
                  AND ST_Within(
                      geom,
                      ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)
                  )
                  AND status = 'available'
                ORDER BY is_featured DESC, created_at DESC
                LIMIT :lim
            """),
            {
                "min_lat": min_lat, "min_lng": min_lng,
                "max_lat": max_lat, "max_lng": max_lng,
                "lim": limit,
            },
        ).fetchall()

        return [
            {
                "id": r[0], "title": r[1], "address": r[2], "price": r[3],
                "property_type": r[4], "lat": r[5], "lng": r[6],
                "commute_score": r[7], "is_featured": r[8],
                "is_verified": r[9], "status": r[10],
            }
            for r in rows
        ]
    except Exception as exc:
        logger.error(f"Viewport search failed: {exc}")
        raise HTTPException(status_code=500, detail="Geo search unavailable")


@app.get("/search/radius")
def search_by_radius(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(5.0),
    limit: int = Query(100),
    db: Session = Depends(get_db),
):
    """PostGIS radius search using ST_DWithin."""
    radius_m = radius_km * 1000
    try:
        rows = db.execute(
            text("""
                SELECT id, title, address, price, property_type, lat, lng,
                       ST_Distance(
                           geom::geography,
                           ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                       ) AS dist_m,
                       commute_score, is_featured
                FROM property.properties
                WHERE geom IS NOT NULL
                  AND ST_DWithin(
                      geom::geography,
                      ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                      :radius
                  )
                  AND status = 'available'
                ORDER BY dist_m ASC
                LIMIT :lim
            """),
            {"lat": lat, "lng": lng, "radius": radius_m, "lim": limit},
        ).fetchall()

        return [
            {
                "id": r[0], "title": r[1], "address": r[2], "price": r[3],
                "property_type": r[4], "lat": r[5], "lng": r[6],
                "distance_m":   round(r[7]) if r[7] is not None else None,
                "commute_score": r[8], "is_featured": r[9],
            }
            for r in rows
        ]
    except Exception as exc:
        logger.error(f"Radius search failed: {exc}")
        raise HTTPException(status_code=500, detail="Geo search unavailable")


@app.get("/search/autocomplete")
async def geo_autocomplete(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """Search autocomplete for localities, stations, and landmarks."""
    results = []

    try:
        rows = db.execute(
            text("""
                SELECT DISTINCT name, category, lat, lng
                FROM geo_amenity.amenity_points
                WHERE LOWER(name) LIKE :query
                ORDER BY name
                LIMIT 10
            """),
            {"query": f"%{q.lower()}%"},
        ).fetchall()
        for r in rows:
            results.append({"name": r[0], "type": r[1], "lat": r[2], "lng": r[3]})
    except Exception as exc:
        logger.warning(f"Autocomplete DB query failed: {exc}")

    try:
        rows = db.execute(
            text("""
                SELECT DISTINCT city, state, lat, lng
                FROM property.properties
                WHERE LOWER(city) LIKE :query OR LOWER(address) LIKE :query
                LIMIT 5
            """),
            {"query": f"%{q.lower()}%"},
        ).fetchall()
        for r in rows:
            if r[0]:
                results.append({
                    "name": f"{r[0]}, {r[1] or 'India'}",
                    "type": "locality",
                    "lat":  r[2],
                    "lng":  r[3],
                })
    except Exception:
        pass

    return results
