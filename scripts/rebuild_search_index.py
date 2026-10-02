import sys
import os
import logging
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database
from search_service import models as search_models
from property_service import models as property_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rebuild_search_index")

def rebuild_search_infrastructure():
    if not shared_database.sync_engine:
        logger.error("Sync Engine is not initialized! Ensure PostgreSQL is running.")
        return False

    with shared_database.sync_engine.connect() as conn:
        try:
            logger.info("Ensuring PostGIS extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()

            logger.info("Creating search schema...")
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS search"))
            conn.commit()

            logger.info("Registering tables...")
            search_models.Base.metadata.create_all(bind=shared_database.sync_engine)

            logger.info("Adding PostGIS and TSVECTOR columns to search.property_index...")
            # We use IF NOT EXISTS equivalents by wrapping in a block or catching exception
            try:
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS geom GEOMETRY(Point, 4326)"))
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS search_vector tsvector"))
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS images TEXT"))
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS locality VARCHAR(256)"))
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS bedrooms INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS bathrooms INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE search.property_index ADD COLUMN IF NOT EXISTS furnishing VARCHAR(64)"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Columns might already exist: {e}")
                conn.rollback()

            logger.info("Creating TSVECTOR and Geometry Indexes...")
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_property_index_geom ON search.property_index USING GIST (geom)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_property_index_search ON search.property_index USING GIN (search_vector)"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Indexes might already exist: {e}")
                conn.rollback()

            logger.info("Creating Triggers for automatic sync...")
            # Function to update TSVECTOR and Geom
            func_sql = """
            CREATE OR REPLACE FUNCTION search.property_index_sync_func() RETURNS trigger AS $$
            BEGIN
                -- Update geom
                IF NEW.lat IS NOT NULL AND NEW.lng IS NOT NULL THEN
                    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326);
                END IF;

                -- Update search_vector
                NEW.search_vector :=
                    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(NEW.address, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(NEW.city, '')), 'C') ||
                    setweight(to_tsvector('english', coalesce(NEW.amenities, '')), 'D');
                
                RETURN NEW;
            END
            $$ LANGUAGE plpgsql;
            """
            conn.execute(text(func_sql))
            conn.commit()

            trigger_sql = """
            DROP TRIGGER IF EXISTS trg_property_index_sync ON search.property_index;
            CREATE TRIGGER trg_property_index_sync
            BEFORE INSERT OR UPDATE ON search.property_index
            FOR EACH ROW EXECUTE PROCEDURE search.property_index_sync_func();
            """
            conn.execute(text(trigger_sql))
            conn.commit()

            logger.info("Triggers created successfully!")

            # Migrate data from property.properties to search.property_index
            logger.info("Synchronizing data from property.properties...")
            db = shared_database.SyncSessionLocal()
            try:
                properties = db.query(property_models.Property).all()
                for p in properties:
                    # Get media count and list
                    media_items = db.query(property_models.PropertyMedia).filter_by(property_id=p.id).all()
                    media_count = len(media_items)
                    images_str = ",".join([m.raw_url for m in media_items if m.raw_url])
                    
                    conn.execute(text("""
                        INSERT INTO search.property_index (
                            property_id, title, description, address, city, state,
                            property_type, price, lat, lng, amenities, is_featured, is_verified,
                            is_furnished, is_pet_friendly, owner_verified, media_count, status,
                            images, locality, bedrooms, bathrooms, furnishing, updated_at
                        ) VALUES (
                            :pid, :title, :desc, :addr, :city, :state,
                            :ptype, :price, :lat, :lng, :amenities, :featured, :verified,
                            :furnished, :pet, :owner_verified, :media, :status,
                            :images, :locality, :bedrooms, :bathrooms, :furnishing, NOW()
                        )
                        ON CONFLICT (property_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            address = EXCLUDED.address,
                            city = EXCLUDED.city,
                            state = EXCLUDED.state,
                            property_type = EXCLUDED.property_type,
                            price = EXCLUDED.price,
                            lat = EXCLUDED.lat,
                            lng = EXCLUDED.lng,
                            amenities = EXCLUDED.amenities,
                            is_featured = EXCLUDED.is_featured,
                            is_verified = EXCLUDED.is_verified,
                            is_furnished = EXCLUDED.is_furnished,
                            is_pet_friendly = EXCLUDED.is_pet_friendly,
                            media_count = EXCLUDED.media_count,
                            status = EXCLUDED.status,
                            images = EXCLUDED.images,
                            locality = EXCLUDED.locality,
                            bedrooms = EXCLUDED.bedrooms,
                            bathrooms = EXCLUDED.bathrooms,
                            furnishing = EXCLUDED.furnishing,
                            updated_at = NOW()
                    """), {
                        "pid": p.id,
                        "title": p.title,
                        "desc": p.description or "",
                        "addr": p.address,
                        "city": p.city or "",
                        "state": p.state or "",
                        "ptype": p.property_type or "",
                        "price": p.price,
                        "lat": p.lat,
                        "lng": p.lng,
                        "amenities": p.amenities or "",
                        "featured": p.is_featured or False,
                        "verified": p.is_verified or False,
                        "furnished": p.is_furnished or False,
                        "pet": p.is_pet_friendly or False,
                        "owner_verified": p.owner_verified or False,
                        "media": media_count,
                        "status": p.status or "available",
                        "images": images_str,
                        "locality": p.address.split(",")[0] if p.address else "",
                        "bedrooms": 2, # Default/fallback for seeded
                        "bathrooms": 2,
                        "furnishing": "semi-furnished"
                    })
                conn.commit()
                logger.info(f"Successfully synchronized {len(properties)} properties to search index.")
            finally:
                db.close()

            return True

        except Exception as e:
            logger.error(f"Error rebuilding search index: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    rebuild_search_infrastructure()
