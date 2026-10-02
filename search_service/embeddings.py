"""
Semantic Search / Embedding Engine — Priority 4 Rentora Search Intelligence
pgvector-based semantic similarity search using MiniLM sentence embeddings.
Falls back to PostgreSQL FTS if model is unavailable.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("embeddings")

MODEL_NAME = "all-MiniLM-L6-v2"   # 384-dim, ~90MB, CPU-friendly
EMBEDDING_DIM = 384
_model = None
_model_available = None


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model, _model_available

    if _model_available is False:
        return None
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
        _model_available = True
        logger.info("✅ Embedding model loaded successfully.")
        return _model
    except ImportError:
        logger.warning("sentence-transformers not installed. Semantic search disabled.")
        _model_available = False
        return None
    except Exception as e:
        logger.warning(f"Embedding model failed to load: {e}. Semantic search disabled.")
        _model_available = False
        return None


def embed_text(text: str) -> Optional[List[float]]:
    """Generate a 384-dim embedding for a text string."""
    model = _get_model()
    if not model:
        return None
    try:
        vec = model.encode(text, convert_to_numpy=True)
        return vec.tolist()
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return None


def embed_property(prop: Dict[str, Any]) -> Optional[List[float]]:
    """Generate an embedding for a property document."""
    text = " ".join(filter(None, [
        prop.get("title"),
        prop.get("description"),
        prop.get("address"),
        prop.get("city"),
        prop.get("amenities"),
        prop.get("property_type"),
    ]))
    return embed_text(text)


def semantic_search(
    query: str,
    db,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Vector similarity search using pgvector cosine distance.
    Falls back to FTS if embedding model unavailable.
    """
    query_vec = embed_text(query)

    if query_vec is None:
        logger.info("Embedding unavailable, falling back to FTS")
        return []

    try:
        from sqlalchemy import text
        vec_str = "[" + ",".join(f"{v:.6f}" for v in query_vec) + "]"
        rows = db.execute(text(f"""
            SELECT property_id, title, address, price, property_type, lat, lng,
                   locality_score, commute_score, is_featured, is_verified,
                   media_count, view_count,
                   1 - (embedding <=> '{vec_str}'::vector) AS cosine_sim
            FROM search.property_index
            WHERE status = 'available'
              AND embedding IS NOT NULL
            ORDER BY embedding <=> '{vec_str}'::vector
            LIMIT :lim
        """), {"lim": limit}).fetchall()

        results = []
        for r in rows:
            results.append({
                "property_id": r[0], "title": r[1], "address": r[2],
                "price": r[3], "property_type": r[4], "lat": r[5], "lng": r[6],
                "locality_score": r[7], "commute_score": r[8],
                "is_featured": r[9], "is_verified": r[10],
                "media_count": r[11], "view_count": r[12],
                "semantic_similarity": round(float(r[13] or 0), 3),
            })

        return results

    except Exception as e:
        logger.warning(f"Semantic search failed: {e}")
        return []


def generate_embeddings_batch(db, batch_size: int = 50) -> int:
    """
    Background job: generate embeddings for properties that don't have one yet.
    Returns number of embeddings generated.
    """
    model = _get_model()
    if not model:
        logger.warning("Embedding model unavailable, skipping batch generation")
        return 0

    count = 0
    try:
        from sqlalchemy import text
        rows = db.execute(text("""
            SELECT property_id, title, description, address, city, amenities, property_type
            FROM search.property_index
            WHERE embedding IS NULL AND status = 'available'
            LIMIT :batch
        """), {"batch": batch_size}).fetchall()

        for row in rows:
            prop = {
                "property_id": row[0], "title": row[1], "description": row[2],
                "address": row[3], "city": row[4], "amenities": row[5], "property_type": row[6],
            }
            vec = embed_property(prop)
            if vec:
                vec_str = "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
                db.execute(text(f"""
                    UPDATE search.property_index
                    SET embedding = '{vec_str}'::vector
                    WHERE property_id = :pid
                """), {"pid": prop["property_id"]})
                count += 1

        db.commit()
        logger.info(f"Generated {count} embeddings")
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        db.rollback()

    return count
