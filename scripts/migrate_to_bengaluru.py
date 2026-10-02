"""
Rentora — Bengaluru Standardisation Migration
===============================================
Migrates all properties that are NOT in Bengaluru (i.e. legacy Goa, Mumbai,
or other city data from early development) to standard Bengaluru defaults.

What this script does:
  1. Identifies rows in property.properties where city is NOT 'Bengaluru'
     (case-insensitive) OR where city is NULL.
  2. Updates those rows to:
       city     = 'Bengaluru'
       state    = 'Karnataka'
       pincode  = '560034'       (Koramangala — central Bengaluru)
       address  = 'Koramangala, Bengaluru'
       lat      = NULL           ← triggers the backfill script to geocode
       lng      = NULL           ← triggers the backfill script to geocode
       geom     = NULL           ← cleared so PostGIS index is consistent
  3. Prints a row-by-row report so you can audit exactly what changed.

Usage:
    # Dry run — see what would change, no DB writes:
    python scripts/migrate_to_bengaluru.py --dry-run

    # Live run:
    python scripts/migrate_to_bengaluru.py

After this script completes, run the coordinate backfill to geocode the
reset rows via Ola Maps:
    python scripts/backfill_bengaluru_coordinates.py --delay 0.3

Requirements:
    DATABASE_URL in .env or shell environment
    psycopg2-binary, sqlalchemy  (already in requirements.txt)
"""

import os
import sys
import argparse
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migrate_to_bengaluru")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Standardise non-Bengaluru properties to Bengaluru defaults."
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would change without writing to the database.")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # ── Load .env ─────────────────────────────────────────────────────────────
    env_path = os.path.join(ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    # ── Database connection ────────────────────────────────────────────────────
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.error("DATABASE_URL is not set. Add it to .env or your shell.")
        sys.exit(1)

    # psycopg2 doesn't understand asyncpg:// or ?currentSchema=
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if "?" in db_url:
        base, qs = db_url.split("?", 1)
        params = [p for p in qs.split("&") if not p.startswith("currentSchema=")]
        db_url = base + ("?" + "&".join(params) if params else "")

    logger.info(f"Connecting to: {db_url.split('@')[-1]}")

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        logger.error("SQLAlchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)

    engine = create_engine(db_url, pool_pre_ping=True)

    # ── Fetch candidate rows ───────────────────────────────────────────────────
    SELECT_SQL = text("""
        SELECT id, title, city, state, address, lat, lng
        FROM property.properties
        WHERE city IS NULL
           OR LOWER(TRIM(city)) <> 'bengaluru'
        ORDER BY id
    """)

    with engine.connect() as conn:
        rows = conn.execute(SELECT_SQL).fetchall()

    if not rows:
        logger.info("No non-Bengaluru properties found. Nothing to migrate.")
        return

    logger.info(
        f"Found {len(rows)} propert{'y' if len(rows) == 1 else 'ies'} to migrate."
        + (" [DRY RUN — no writes]" if args.dry_run else "")
    )

    # ── Migrate row by row ─────────────────────────────────────────────────────
    migrated = 0
    UPDATE_SQL = text("""
        UPDATE property.properties
        SET city    = 'Bengaluru',
            state   = 'Karnataka',
            pincode = '560034',
            address = 'Koramangala, Bengaluru',
            lat     = NULL,
            lng     = NULL,
            geom    = NULL
        WHERE id = :id
    """)

    for row in rows:
        prop_id, title, city, state, address, lat, lng = row
        logger.info(
            f"  Property #{prop_id}: '{title or '(no title)'}' | "
            f"city='{city or 'NULL'}' lat={lat} lng={lng}"
            f"{' → DRY RUN' if args.dry_run else ' → Bengaluru (lat/lng cleared)'}"
        )

        if not args.dry_run:
            with engine.connect() as conn:
                conn.execute(UPDATE_SQL, {"id": prop_id})
                conn.commit()
            migrated += 1

    # ── Summary ────────────────────────────────────────────────────────────────
    logger.info("─" * 56)
    if args.dry_run:
        logger.info(f"DRY RUN complete: {len(rows)} rows would be updated.")
        logger.info("Re-run without --dry-run to apply changes.")
    else:
        logger.info(f"Migration complete: {migrated}/{len(rows)} rows updated.")
        logger.info(
            "Next step — re-geocode the cleared rows:\n"
            "  python scripts/backfill_bengaluru_coordinates.py --delay 0.3"
        )


if __name__ == "__main__":
    main()
