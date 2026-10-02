"""
Rentora — Bengaluru Coordinate Backfill Script
===============================================
Idempotent script that finds all properties in the `property.properties`
table that are missing lat/lng coordinates and resolves them via the
Ola Maps Geocode API (Bengaluru-biased bounding box).

Usage:
    # Dry-run (shows what would be updated, no DB writes):
    python scripts/backfill_bengaluru_coordinates.py --dry-run

    # Live run:
    python scripts/backfill_bengaluru_coordinates.py

    # Limit to first N rows (useful for testing):
    python scripts/backfill_bengaluru_coordinates.py --limit 20

Environment:
    OLA_MAPS_API_KEY  — must be set in .env or shell environment.
    DATABASE_URL      — read from .env via shared_database.

Safety:
    - Only modifies rows where lat IS NULL or lng IS NULL.
    - Writes are committed property-by-property so a mid-run failure
      does not roll back already-resolved coordinates.
    - Running the script multiple times is safe (rows with coordinates
      are skipped entirely).
"""

import os
import sys
import asyncio
import argparse
import logging
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backfill_coords")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill lat/lng for Bengaluru properties.")
    p.add_argument("--dry-run", action="store_true", help="Print changes without writing to DB.")
    p.add_argument("--limit", type=int, default=0, help="Process at most N rows (0 = all).")
    p.add_argument("--delay", type=float, default=0.3,
                   help="Seconds to wait between API calls (rate-limit courtesy).")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Geocoder (inline, no service import dependency)
# ---------------------------------------------------------------------------

async def _geocode(session, address: str, area: str, city: str, pincode: str, api_key: str):
    """Call Ola Maps Geocode API and return (lat, lng) or (None, None)."""
    import httpx

    parts = [p.strip() for p in [address, area, city, "Karnataka", pincode, "India"] if p and p.strip()]
    deduped = [parts[0]] + [b for a, b in zip(parts, parts[1:]) if a.lower() != b.lower()]
    query = ", ".join(deduped)

    params = {
        "address":  query,
        "bounds":   "12.7342,77.3791|13.1739,77.8280",
        "language": "en",
        "api_key":  api_key,
    }

    try:
        resp = await session.get(
            "https://api.olamaps.io/places/v1/geocode",
            params=params,
        )
        if resp.status_code != 200:
            logger.warning(f"  HTTP {resp.status_code} for '{query}'")
            return None, None

        results = resp.json().get("geocodingResults") or resp.json().get("results") or []
        if not results:
            logger.warning(f"  No results for '{query}'")
            return None, None

        loc = results[0].get("geometry", {}).get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng") or loc.get("lon")
        return (float(lat), float(lng)) if lat and lng else (None, None)
    except Exception as exc:
        logger.error(f"  Geocode error for '{query}': {exc}")
        return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    args = parse_args()

    api_key = os.environ.get("OLA_MAPS_API_KEY", "")
    if not api_key:
        # Try loading from .env manually
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OLA_MAPS_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break

    if not api_key:
        logger.error("OLA_MAPS_API_KEY is not set. Aborting.")
        sys.exit(1)

    import shared_database
    from sqlalchemy import text

    if not shared_database.sync_engine:
        logger.error("sync_engine unavailable — check DATABASE_URL.")
        sys.exit(1)

    # Fetch properties missing coordinates
    with shared_database.sync_engine.connect() as conn:
        query = """
            SELECT id, address, area, city, pincode
            FROM property.properties
            WHERE lat IS NULL OR lng IS NULL
            ORDER BY id ASC
        """
        if args.limit > 0:
            query += f" LIMIT {args.limit}"
        rows = conn.execute(text(query)).fetchall()

    total = len(rows)
    if total == 0:
        logger.info("No properties with missing coordinates. Nothing to do.")
        return

    logger.info(
        f"Found {total} properties with missing coordinates."
        + (" [DRY RUN — no writes]" if args.dry_run else "")
    )

    resolved = 0
    failed = 0

    import httpx
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=4.0)) as session:
        for i, row in enumerate(rows, 1):
            prop_id, address, area, city, pincode = row
            logger.info(f"[{i}/{total}] Property #{prop_id}: '{address}'")

            lat, lng = await _geocode(
                session,
                address=address or "",
                area=area or "",
                city=city or "Bengaluru",
                pincode=pincode or "",
                api_key=api_key,
            )

            if lat is None:
                logger.warning(f"  → Could not resolve. Skipping.")
                failed += 1
            elif args.dry_run:
                logger.info(f"  → [DRY RUN] Would set lat={lat:.5f}, lng={lng:.5f}")
                resolved += 1
            else:
                with shared_database.sync_engine.connect() as conn:
                    conn.execute(
                        text("""
                            UPDATE property.properties
                            SET lat = :lat,
                                lng = :lng,
                                geom = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                            WHERE id = :id
                        """),
                        {"lat": lat, "lng": lng, "id": prop_id},
                    )
                    conn.commit()
                logger.info(f"  → Updated lat={lat:.5f}, lng={lng:.5f}")
                resolved += 1

            if args.delay > 0 and i < total:
                await asyncio.sleep(args.delay)

    # Summary
    logger.info("─" * 50)
    logger.info(
        f"Backfill complete: {resolved} resolved, {failed} skipped, "
        f"{total - resolved - failed} remaining."
    )
    if args.dry_run:
        logger.info("DRY RUN — re-run without --dry-run to commit changes.")


if __name__ == "__main__":
    asyncio.run(main())
