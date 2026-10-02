"""
Rentora — Property Geo Columns Migration
==========================================
Safely adds the geo-enrichment columns to property.properties that were
introduced in the Phase 1 geocoding update but never applied to the live DB.

All statements use ADD COLUMN IF NOT EXISTS so the script is fully idempotent —
running it multiple times is safe and will not raise errors on already-existing
columns.

Usage:
    python scripts/migrate_property_geo_columns.py

Requires:
    DATABASE_URL in .env  (or already set in the shell environment)
    psycopg2-binary       (already present in requirements.txt)
"""

import os
import sys
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migrate_property_geo_columns")

# ---------------------------------------------------------------------------
# Migration statements — ordered, idempotent
# ---------------------------------------------------------------------------

MIGRATIONS = [
    # Granular address fields needed by the Bengaluru geocoder
    ("area column",    "ALTER TABLE property.properties ADD COLUMN IF NOT EXISTS area    VARCHAR(255);"),
    ("city column",    "ALTER TABLE property.properties ADD COLUMN IF NOT EXISTS city    VARCHAR(255);"),
    ("state column",   "ALTER TABLE property.properties ADD COLUMN IF NOT EXISTS state   VARCHAR(255) DEFAULT 'Karnataka';"),
    ("pincode column", "ALTER TABLE property.properties ADD COLUMN IF NOT EXISTS pincode VARCHAR(50);"),
    # Coordinate columns (may already exist on older deploys without the geo update)
    ("lat column",     "ALTER TABLE property.properties ADD COLUMN IF NOT EXISTS lat     DOUBLE PRECISION;"),
    ("lng column",     "ALTER TABLE property.properties ADD COLUMN IF NOT EXISTS lng     DOUBLE PRECISION;"),
    # PostGIS geometry column — requires the postgis extension (already present)
    ("geom column", """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'property'
                  AND table_name   = 'properties'
                  AND column_name  = 'geom'
            ) THEN
                ALTER TABLE property.properties
                    ADD COLUMN geom geometry(Point, 4326);
            END IF;
        END $$;
    """),
    # Spatial index — safe to re-run (IF NOT EXISTS)
    ("spatial index", """
        CREATE INDEX IF NOT EXISTS idx_properties_geom
            ON property.properties USING GIST (geom);
    """),
    # Back-fill geom from any lat/lng that already exist
    ("backfill geom", """
        UPDATE property.properties
           SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
         WHERE lat IS NOT NULL
           AND lng IS NOT NULL
           AND geom IS NULL;
    """),
]


def main() -> None:
    # ── Load .env manually so the script works outside Docker ────────────────
    env_path = os.path.join(ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

    # ── Resolve DATABASE_URL ─────────────────────────────────────────────────
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.error("DATABASE_URL is not set. Add it to .env or your shell environment.")
        sys.exit(1)

    # psycopg2 (sync) requires postgresql:// not postgresql+asyncpg://
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        logger.info("Converted async URL to sync for psycopg2.")

    # Strip currentSchema param — psycopg2 doesn't understand it
    if "?" in db_url:
        base, qs = db_url.split("?", 1)
        params = [p for p in qs.split("&") if not p.startswith("currentSchema=")]
        db_url = base + ("?" + "&".join(params) if params else "")

    logger.info(f"Connecting to: {db_url.split('@')[-1]}")  # log host only, hide creds

    # ── Connect and run migrations ───────────────────────────────────────────
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        logger.error("SQLAlchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)

    engine = create_engine(db_url, pool_pre_ping=True)

    total   = len(MIGRATIONS)
    applied = 0
    failed  = 0

    with engine.connect() as conn:
        for i, (label, sql) in enumerate(MIGRATIONS, 1):
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"  [{i}/{total}] ✅  {label}")
                applied += 1
            except Exception as exc:
                conn.rollback()
                logger.warning(f"  [{i}/{total}] ⚠️  {label} — {exc}")
                failed += 1

    logger.info("─" * 50)
    logger.info(f"Migration complete: {applied} applied, {failed} skipped/warned.")
    if failed:
        logger.warning(
            "Some steps produced warnings. This is usually harmless (column already exists). "
            "Review the messages above to confirm."
        )
    else:
        logger.info("All steps applied cleanly. You can now run the backfill script.")


if __name__ == "__main__":
    main()
