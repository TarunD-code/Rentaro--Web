"""
PostGIS Spatial Architecture Initialization Script
Adds geometry columns, spatial indexes, and amenity reference tables.
Run AFTER the base PostgreSQL tables have been created.
"""
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("initialize_postgis")

SQL_COMMANDS = [
    # 1. Ensure PostGIS extension
    "CREATE EXTENSION IF NOT EXISTS postgis;",

    # 2. Add geometry column to properties if not exists
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'property' AND table_name = 'properties' AND column_name = 'geom'
        ) THEN
            ALTER TABLE property.properties ADD COLUMN geom geometry(Point, 4326);
        END IF;
    END $$;
    """,

    # 3. Populate geom from existing lat/lng
    """
    UPDATE property.properties
    SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    WHERE lat IS NOT NULL AND lng IS NOT NULL AND geom IS NULL;
    """,

    # 4. GIST spatial index on properties
    """
    CREATE INDEX IF NOT EXISTS idx_properties_geom
    ON property.properties USING GIST (geom);
    """,

    # 5. Create geo_amenity schema
    "CREATE SCHEMA IF NOT EXISTS geo_amenity;",

    # 6. Amenity points table
    # osm_id is TEXT to accommodate both legacy OSM integer IDs and
    # Ola Maps string place_ids (e.g. "ChIJ...").
    """
    CREATE TABLE IF NOT EXISTS geo_amenity.amenity_points (
        id SERIAL PRIMARY KEY,
        osm_id TEXT,
        name VARCHAR(512) NOT NULL,
        category VARCHAR(64) NOT NULL,
        subcategory VARCHAR(128),
        lat DOUBLE PRECISION NOT NULL,
        lng DOUBLE PRECISION NOT NULL,
        geom geometry(Point, 4326),
        source VARCHAR(32) DEFAULT 'ola_maps',
        raw_tags JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(osm_id, category)
    );
    """,

    # 6b. Migrate existing BIGINT osm_id column to TEXT if the table already exists
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

    # 7. GIST index on amenity_points
    """
    CREATE INDEX IF NOT EXISTS idx_amenity_points_geom
    ON geo_amenity.amenity_points USING GIST (geom);
    """,

    # 8. Category index for fast category filtering
    """
    CREATE INDEX IF NOT EXISTS idx_amenity_points_category
    ON geo_amenity.amenity_points (category);
    """,

    # 9. Locality boundaries table
    """
    CREATE TABLE IF NOT EXISTS geo_amenity.locality_boundaries (
        id SERIAL PRIMARY KEY,
        name VARCHAR(256) NOT NULL,
        city VARCHAR(128),
        state VARCHAR(128),
        boundary_type VARCHAR(64) DEFAULT 'locality',
        geom geometry(Polygon, 4326),
        population INTEGER,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # 10. GIST index on locality boundaries
    """
    CREATE INDEX IF NOT EXISTS idx_locality_boundaries_geom
    ON geo_amenity.locality_boundaries USING GIST (geom);
    """,

    # 11. Locality scores table
    """
    CREATE TABLE IF NOT EXISTS geo_amenity.locality_scores (
        id SERIAL PRIMARY KEY,
        locality_id INTEGER REFERENCES geo_amenity.locality_boundaries(id),
        property_id INTEGER,
        metro_score FLOAT DEFAULT 0,
        hospital_score FLOAT DEFAULT 0,
        school_score FLOAT DEFAULT 0,
        grocery_score FLOAT DEFAULT 0,
        office_score FLOAT DEFAULT 0,
        park_score FLOAT DEFAULT 0,
        lifestyle_score FLOAT DEFAULT 0,
        walkability_score FLOAT DEFAULT 0,
        transit_score FLOAT DEFAULT 0,
        family_score FLOAT DEFAULT 0,
        overall_score FLOAT DEFAULT 0,
        computed_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # 12. Commute matrix cache table
    """
    CREATE TABLE IF NOT EXISTS geo_amenity.commute_matrix (
        id SERIAL PRIMARY KEY,
        origin_lat DOUBLE PRECISION NOT NULL,
        origin_lng DOUBLE PRECISION NOT NULL,
        dest_lat DOUBLE PRECISION NOT NULL,
        dest_lng DOUBLE PRECISION NOT NULL,
        mode VARCHAR(32) DEFAULT 'driving',
        distance_km FLOAT,
        duration_min FLOAT,
        route_polyline TEXT,
        computed_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # 13. Index on commute matrix for fast origin lookups
    """
    CREATE INDEX IF NOT EXISTS idx_commute_origin
    ON geo_amenity.commute_matrix (origin_lat, origin_lng);
    """,
]


def initialize_postgis():
    logger.info("Initializing PostGIS spatial architecture...")

    if not shared_database.sync_engine:
        logger.error("Sync engine not available. Ensure PostgreSQL is running.")
        return False

    try:
        from sqlalchemy import text
        with shared_database.sync_engine.connect() as conn:
            for i, sql in enumerate(SQL_COMMANDS):
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"  ✅ Step {i+1}/{len(SQL_COMMANDS)} executed successfully.")
                except Exception as e:
                    logger.warning(f"  ⚠️ Step {i+1}/{len(SQL_COMMANDS)} warning: {e}")
                    conn.rollback()

        logger.info("PostGIS spatial architecture initialization complete!")
        return True
    except Exception as e:
        logger.error(f"PostGIS initialization failed: {e}")
        return False


if __name__ == "__main__":
    initialize_postgis()
