"""
Extended PostGIS + pgvector + FTS Initialization Script (Priority 4 additions).
Run after the base initialize_postgis.py to add search intelligence columns.
"""
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("initialize_search_schema")

SEARCH_SQL = [
    # 1. pg_trgm for fuzzy matching
    "CREATE EXTENSION IF NOT EXISTS pg_trgm;",

    # 2. pgvector for semantic search
    "CREATE EXTENSION IF NOT EXISTS vector;",

    # 3. Create search schema
    "CREATE SCHEMA IF NOT EXISTS search;",

    # 4. Add tsvector column to properties if not exists
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='property' AND table_name='properties' AND column_name='search_vector'
        ) THEN
            ALTER TABLE property.properties
            ADD COLUMN search_vector tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(address, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(city, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(amenities, '')), 'D')
            ) STORED;
        END IF;
    END $$;
    """,

    # 5. GIN index on search_vector for fast FTS
    """
    CREATE INDEX IF NOT EXISTS idx_properties_search_vector
    ON property.properties USING GIN (search_vector);
    """,

    # 6. Trigram index on title for fuzzy matching
    """
    CREATE INDEX IF NOT EXISTS idx_properties_title_trgm
    ON property.properties USING GIN (title gin_trgm_ops);
    """,

    # 7. Trigram index on address for locality fuzzy matching
    """
    CREATE INDEX IF NOT EXISTS idx_properties_address_trgm
    ON property.properties USING GIN (address gin_trgm_ops);
    """,

    # 8. Property search index table (denormalized for ranking)
    """
    CREATE TABLE IF NOT EXISTS search.property_index (
        id SERIAL PRIMARY KEY,
        property_id INTEGER NOT NULL UNIQUE,
        title VARCHAR(512) NOT NULL,
        description TEXT,
        address TEXT,
        city VARCHAR(128),
        state VARCHAR(128),
        property_type VARCHAR(64),
        price FLOAT,
        lat DOUBLE PRECISION,
        lng DOUBLE PRECISION,
        amenities TEXT,
        is_featured BOOLEAN DEFAULT FALSE,
        is_verified BOOLEAN DEFAULT FALSE,
        is_furnished BOOLEAN DEFAULT FALSE,
        is_pet_friendly BOOLEAN DEFAULT FALSE,
        owner_verified BOOLEAN DEFAULT FALSE,
        locality_score FLOAT DEFAULT 0,
        commute_score FLOAT DEFAULT 0,
        metro_score FLOAT DEFAULT 0,
        hospital_score FLOAT DEFAULT 0,
        school_score FLOAT DEFAULT 0,
        walkability_score FLOAT DEFAULT 0,
        popularity_score FLOAT DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        contact_count INTEGER DEFAULT 0,
        favorite_count INTEGER DEFAULT 0,
        avg_rating FLOAT DEFAULT 0,
        media_count INTEGER DEFAULT 0,
        tags TEXT,
        status VARCHAR(32) DEFAULT 'available',
        embedding vector(384),
        indexed_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # 9. GIN FTS index on property_index
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='search' AND tablename='property_index' AND indexname='idx_search_index_fts') THEN
            CREATE INDEX idx_search_index_fts
            ON search.property_index
            USING GIN (to_tsvector('english',
                coalesce(title,'') || ' ' || coalesce(description,'') || ' ' ||
                coalesce(address,'') || ' ' || coalesce(city,'') || ' ' || coalesce(amenities,'')
            ));
        END IF;
    END $$;
    """,

    # 10. IVFFlat index on embeddings for ANN search
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='search' AND tablename='property_index' AND indexname='idx_search_embedding') THEN
            CREATE INDEX idx_search_embedding
            ON search.property_index
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 10);
        END IF;
    END $$;
    """,

    # 11. Autocomplete index table
    """
    CREATE TABLE IF NOT EXISTS search.autocomplete_index (
        id SERIAL PRIMARY KEY,
        term VARCHAR(256) NOT NULL,
        term_type VARCHAR(64) NOT NULL,
        display_name VARCHAR(512),
        lat DOUBLE PRECISION,
        lng DOUBLE PRECISION,
        search_count INTEGER DEFAULT 0,
        UNIQUE(term, term_type)
    );
    """,

    # 12. Trigram index on autocomplete terms
    """
    CREATE INDEX IF NOT EXISTS idx_autocomplete_trgm
    ON search.autocomplete_index USING GIN (term gin_trgm_ops);
    """,

    # 13. Search analytics events table
    """
    CREATE TABLE IF NOT EXISTS search.analytics_events (
        id BIGSERIAL PRIMARY KEY,
        event_type VARCHAR(64) NOT NULL,
        user_id VARCHAR(256),
        session_id VARCHAR(256),
        property_id INTEGER,
        search_query TEXT,
        filters_json TEXT,
        result_count INTEGER,
        position_clicked INTEGER,
        dwell_seconds INTEGER,
        ip_hash VARCHAR(64),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # 14. Index on analytics events for user/property lookups
    """
    CREATE INDEX IF NOT EXISTS idx_analytics_user_id
    ON search.analytics_events (user_id) WHERE user_id IS NOT NULL;
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_analytics_property_id
    ON search.analytics_events (property_id) WHERE property_id IS NOT NULL;
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_analytics_event_type
    ON search.analytics_events (event_type, created_at DESC);
    """,

    # 15. Search history table (per user)
    """
    CREATE TABLE IF NOT EXISTS search.search_history (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(256) NOT NULL,
        query TEXT NOT NULL,
        filters_json TEXT,
        result_count INTEGER,
        searched_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_search_history_user
    ON search.search_history (user_id, searched_at DESC);
    """,

    # 16. Seed autocomplete with Indian metro cities and common localities
    """
    INSERT INTO search.autocomplete_index (term, term_type, display_name, lat, lng) VALUES
        ('whitefield', 'locality', 'Whitefield, Bengaluru', 12.9698, 77.7499),
        ('koramangala', 'locality', 'Koramangala, Bengaluru', 12.9352, 77.6245),
        ('indiranagar', 'locality', 'Indiranagar, Bengaluru', 12.9719, 77.6412),
        ('bandra west', 'locality', 'Bandra West, Mumbai', 19.0596, 72.8295),
        ('powai', 'locality', 'Powai, Mumbai', 19.1176, 72.9060),
        ('hiranandani', 'locality', 'Hiranandani Gardens, Powai', 19.1197, 72.9062),
        ('gurgaon', 'locality', 'Gurugram, Haryana', 28.4595, 77.0266),
        ('cyber city', 'office_hub', 'DLF Cyber City, Gurgaon', 28.4944, 77.0879),
        ('manyata tech park', 'office_hub', 'Manyata Tech Park, Bengaluru', 13.0475, 77.6209),
        ('electronic city', 'locality', 'Electronic City, Bengaluru', 12.8452, 77.6602),
        ('salt lake', 'locality', 'Salt Lake City, Kolkata', 22.5726, 88.4139),
        ('hsr layout', 'locality', 'HSR Layout, Bengaluru', 12.9116, 77.6473),
        ('btm layout', 'locality', 'BTM Layout, Bengaluru', 12.9166, 77.6101),
        ('marathahalli', 'locality', 'Marathahalli, Bengaluru', 12.9591, 77.6974),
        ('andheri west', 'locality', 'Andheri West, Mumbai', 19.1367, 72.8296),
        ('sector 62 noida', 'locality', 'Sector 62, Noida', 28.6206, 77.3645),
        ('madhapur', 'locality', 'Madhapur, Hyderabad', 17.4486, 78.3908),
        ('hitech city', 'office_hub', 'HITEC City, Hyderabad', 17.4435, 78.3772)
    ON CONFLICT (term, term_type) DO NOTHING;
    """,
]


def initialize_search_schema():
    logger.info("Initializing Priority 4 Search Intelligence schema...")

    if not shared_database.sync_engine:
        logger.error("Sync engine not available.")
        return False

    try:
        from sqlalchemy import text
        with shared_database.sync_engine.connect() as conn:
            for i, sql in enumerate(SEARCH_SQL):
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"  ✅ Step {i+1}/{len(SEARCH_SQL)} OK")
                except Exception as e:
                    logger.warning(f"  ⚠️ Step {i+1} warning (continuing): {e}")
                    conn.rollback()

        logger.info("✅ Search Intelligence schema initialization complete!")
        return True
    except Exception as e:
        logger.error(f"❌ Search schema initialization failed: {e}")
        return False


if __name__ == "__main__":
    initialize_search_schema()
