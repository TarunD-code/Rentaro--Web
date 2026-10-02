import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_search_index")

def build_index():
    logger.info("Starting one-shot search index build...")
    try:
        import shared_database
        from sqlalchemy import text

        with shared_database.sync_engine.connect() as conn:
            # 1. Clear existing index
            conn.execute(text("TRUNCATE TABLE search.property_index RESTART IDENTITY CASCADE"))
            logger.info("Cleared existing search index")
            
            # 2. Insert all available properties
            res = conn.execute(text("""
                INSERT INTO search.property_index (
                    property_id, title, description, address, city, state,
                    property_type, price, lat, lng, amenities, is_featured, is_verified,
                    is_furnished, is_pet_friendly, owner_verified,
                    status, indexed_at, updated_at
                )
                SELECT 
                    id, title, description, address, city, state,
                    property_type, base_price, lat, lng, amenities, is_featured, is_verified,
                    is_furnished, is_pet_friendly, TRUE,
                    status, NOW(), NOW()
                FROM property.properties
                WHERE status = 'available'
            """))
            conn.commit()
            logger.info(f"Inserted {res.rowcount} properties into search index")
            
            # 3. Update locality scores if available
            res = conn.execute(text("""
                UPDATE search.property_index pi
                SET locality_score = COALESCE(ls.overall_score, 0),
                    metro_score = COALESCE(ls.metro_score, 0),
                    hospital_score = COALESCE(ls.hospital_score, 0),
                    school_score = COALESCE(ls.school_score, 0),
                    walkability_score = COALESCE(ls.walkability_score, 0)
                FROM geo_amenity.locality_scores ls
                WHERE pi.property_id = ls.property_id
            """))
            conn.commit()
            logger.info(f"Updated locality scores for {res.rowcount} properties")

        logger.info("✅ Search index build complete. Now generating embeddings...")
        
        # 4. Generate embeddings
        try:
            from search_service.database import SessionLocal
            from search_service.embeddings import generate_embeddings_batch
            db = SessionLocal()
            total_embeddings = 0
            while True:
                count = generate_embeddings_batch(db, batch_size=50)
                total_embeddings += count
                if count == 0:
                    break
            logger.info(f"✅ Generated {total_embeddings} embeddings.")
        except ImportError:
            logger.warning("Could not load embedding module. Skipping embeddings.")

    except Exception as e:
        logger.error(f"Search index build failed: {e}")

if __name__ == "__main__":
    build_index()
