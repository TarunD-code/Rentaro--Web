# Implementation Plan: Priority 4 — Search, Discovery & Recommendation Intelligence Platform

## Background

Rentora has a solid geo-intelligent foundation (PostgreSQL+PostGIS, Redis, RabbitMQ, MapLibre, geo_amenity_service). The current search is basic SQLAlchemy LIKE queries in `property_service/main.py` with MapTiler autocomplete. This plan transforms search into an enterprise-grade intelligence platform.

---

## 🔍 Codebase Discovery Summary

### Current Search State
| Component | Current Implementation | Gap |
|-----------|----------------------|-----|
| Autocomplete | MapTiler API geocoding | No property/locality-aware suggestions |
| Full-text search | SQLAlchemy `LIKE` queries | No fuzzy, no stemming, no relevance |
| Filtering | URL params → SQL filters | Missing commute score, locality score filters |
| Ranking | `ORDER BY is_featured, created_at` | No intelligence, no behavioral signals |
| Recommendations | None | Entirely missing |
| Analytics | Console.log stubs | No event capture, no behavioral tracking |
| Autocomplete backend | `/property/search/suggestions` → MapTiler | No property/name/landmark awareness |

### Key Files Identified
- `frontend/src/pages/Listings.tsx` — main search UI (443 lines, good structure to extend)
- `frontend/src/components/SearchBar.tsx` — suggestion dropdown (extend in-place)
- `frontend/src/components/HeroSearch.tsx` — hero search (extend with trending/suggestions)
- `frontend/src/api/properties.ts` — thin API layer (extend with search API)
- `frontend/src/hooks/useDebounce.ts` — already has debounce hook
- `property_service/main.py` — primary search endpoint to extend
- `shared_redis.py` — robust Redis layer with fallback (extend with analytics keys)
- `shared_event_broker.py` — RabbitMQ with DLX/DLQ (add search events)
- `geo_amenity_service/main.py` — locality scores already computed (feed into ranking)
- `requirements.txt` — no search/ML libraries yet (add `opensearch-py`, `qdrant-client`)

---

## ⚠️ User Review Required

> [!IMPORTANT]
> **OpenSearch vs. PostgreSQL Full-Text Search Decision**
>
> Running a full OpenSearch/Elasticsearch cluster adds significant infrastructure complexity and hardware requirements (~2GB RAM per node). 
> 
> **Recommended pragmatic approach** for this stage:
> - **Phase A (this implementation)**: Use **PostgreSQL Full-Text Search** (`tsvector`/`tsquery`) + `pg_trgm` (trigram fuzzy matching) for all search capabilities. This is fully sufficient for 100k-500k listings, integrates cleanly with the existing stack, needs no new infrastructure, and is **production-ready**.
> - **Phase B (future)**: Migrate hot indexes to OpenSearch when query volume exceeds PostgreSQL capacity thresholds.
>
> This avoids premature infrastructure complexity while delivering **all the enterprise search features** (fuzzy, stemming, ranking, autocomplete) you need right now.

> [!IMPORTANT]
> **Vector Search: pgvector vs. Qdrant**
>
> Qdrant requires a separate containerized service. For the current property count, **pgvector extension** within the existing PostgreSQL container is sufficient and simpler.
>
> We will: install pgvector in the PostGIS container, add `vector(384)` columns for property embeddings, and build a **semantic search foundation** that is API-compatible with Qdrant for future migration.

> [!WARNING]
> **Behavioral Analytics Data Volume**
>
> Tracking every property view/click will generate very high write volumes. We will use **RabbitMQ buffering** + **async batch upserts** to PostgreSQL, not inline writes, to prevent blocking request paths.

---

## Open Questions

> [!NOTE]
> 1. Should the `recommendation_service` run as a standalone microservice (port 8015) or as an extended module within `search_service`?
> 2. Should behavioral analytics be stored in `property.analytics_events` table or a dedicated `analytics` schema?
> 3. Do you want the **frontend Discovery UX** (trending, recommended, similar properties) on the Home page, Listings page, or both?
> 4. Should OpenSearch be added to docker-compose immediately (for future readiness), or deferred to Phase B?

---

## Proposed Changes

### Part 1 — PostgreSQL Full-Text Search Foundation

#### [MODIFY] `scripts/initialize_postgis.py`
- Add `pg_trgm` extension enablement
- Add `tsvector` generated columns to `property.properties` for full-text indexing
- Add GIN index on the tsvector column for O(1) full-text lookups
- Add trigram GIN index for fuzzy matching

#### [NEW] `search_service/__init__.py`
#### [NEW] `search_service/database.py` — sync engine on `search` schema
#### [NEW] `search_service/models.py` — SearchHistory, PopularSearch, SearchAnalytics models
#### [NEW] `search_service/schemas.py` — Pydantic models for search requests/responses
#### [NEW] `search_service/ranking_engine.py` — weighted ranking logic
#### [NEW] `search_service/main.py` — FastAPI app on port 8015 with all search endpoints

---

### Part 2 — Property Search Document & Indexing

#### [MODIFY] `property_service/main.py`
- Replace basic LIKE search with PostgreSQL FTS using `to_tsvector` + `to_tsquery`
- Add fuzzy matching via `pg_trgm` `similarity()` function
- Auto-update `search_vector` column on property create/update
- Publish `property_index_updated` event to RabbitMQ on every write

#### [NEW] `search_service/index_worker.py`
- RabbitMQ consumer listening to: `property_created`, `property_updated`, `property_deleted`, `locality_score_updated`
- Upserts denormalized search documents into `search.property_index` table
- Idempotent processing via Redis event deduplication (reuses `shared_event_broker` pattern)

#### [NEW] `scripts/build_search_index.py`
- One-shot script to bulk-reindex all existing properties into `search.property_index`

---

### Part 3 — Advanced Search Capabilities (search_service endpoints)

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/search/properties` | Full enterprise search with all filters |
| `GET` | `/search/autocomplete` | Instant prefix + fuzzy autocomplete |
| `GET` | `/search/suggestions` | Contextual query suggestions |
| `GET` | `/search/trending` | Trending searches (Redis sorted set) |
| `POST` | `/search/track` | Track a search query event |

**Search Filters Supported:**
- `q` — keyword + FTS + fuzzy
- `min_price` / `max_price`
- `property_type`
- `bhk` (1BHK, 2BHK, 3BHK, 4BHK)
- `furnished` (true/false)
- `pet_friendly`
- `locality_score_min` (0-10)
- `commute_score_min`
- `near_lat` / `near_lng` / `radius_km` (PostGIS)
- `min_lat` / `max_lat` / `min_lng` / `max_lng` (viewport)
- `metro_corridor` (station name → nearby properties)
- `office_hub` (tech park name → commute-filtered)
- `sort_by` (relevance | price | locality_score | commute_score | freshness)
- `ranking_profile` (family | student | it_professional | luxury | short_stay)
- `page` / `page_size` (pagination)

---

### Part 4 — Intelligent Ranking Engine

#### [NEW] `search_service/ranking_engine.py`
Scoring formula:
```
final_score = (
    text_relevance    × 0.25  +
    locality_score    × 0.20  +
    commute_score     × 0.15  +
    freshness_score   × 0.10  +
    engagement_score  × 0.10  +
    amenity_score     × 0.10  +
    media_quality     × 0.05  +
    owner_rating      × 0.05
)
```
- Configurable **ranking profiles** (family/student/IT/luxury/short-stay) adjust weights
- Dynamic **boost multipliers** for featured, verified, highly-viewed, quick-responder listings
- All weights configurable via environment variables (no hardcoding)

---

### Part 5 — Autocomplete & Trending

#### [NEW] `search_service/autocomplete.py`
- Prefix search on `search.autocomplete_index` table (localities, stations, landmarks, property names)
- Fuzzy match via pg_trgm `%` operator with `similarity > 0.3` threshold
- Redis-cached autocomplete results (5 min TTL, key: `autocomplete:{prefix}`)
- Trending queries stored in Redis sorted set `search:trending` (ZADD/ZREVRANGE)
- Personalized suggestions via user's search history (if authenticated)
- Contextual suggestion templates: `"near {office}", "family-friendly in {locality}"`

---

### Part 6 — Behavioral Analytics Engine

#### [NEW] `search_service/analytics.py`
Events tracked (all async via RabbitMQ):
- `property_viewed` — property ID, user ID (optional), session ID, dwell time
- `property_clicked` — from search results, position in list
- `property_favorited`
- `search_performed` — query text, filters, result count
- `contact_initiated` — property ID, owner ID
- `visit_booked`
- `page_view` — page, referrer

#### [NEW] `search_service/analytics_worker.py`
- RabbitMQ consumer for `analytics.*` events
- Batch upsert to `search.analytics_events` table (every 50 events or 5 seconds)
- Update Redis popularity scores: `ZINCRBY search:popular:{property_id} 1`

---

### Part 7 — Recommendation Engine

#### [NEW] `search_service/recommendations.py`
**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/recommendations/similar/{property_id}` | Content-based similarity |
| `GET` | `/recommendations/for-you` | User preference-based (auth required) |
| `GET` | `/recommendations/trending/{locality}` | Popular in locality |
| `GET` | `/recommendations/office/{office_name}` | Best commute to office |
| `GET` | `/recommendations/people-also-viewed/{id}` | Collaborative filter |

**Algorithms:**
- **Content-based**: Jaccard similarity on amenity sets + price band matching + locality score proximity
- **Collaborative**: Co-view matrix from `analytics_events` (users who viewed X also viewed Y)
- **Commute-based**: Properties with commute score ≥ user's preferred office within 30 mins
- **Locality affinity**: User's last 10 search localities → boost matching properties

All recommendations cached in Redis (30 min TTL).

---

### Part 8 — Vector Search Foundation (pgvector)

#### [MODIFY] `scripts/initialize_postgis.py`
- Enable `pgvector` extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Add `embedding vector(384)` column to `search.property_index`
- Create IVFFlat index for approximate nearest neighbor search

#### [NEW] `search_service/embeddings.py`
- Lightweight sentence embedding using `sentence-transformers` (MiniLM-L6-v2 model, 384-dim)
- Batch embedding generation for property descriptions
- Semantic search endpoint: `GET /search/semantic?q=family+apartment+near+metro`
- Graceful fallback to keyword search if embedding model unavailable

> [!NOTE]
> MiniLM-L6-v2 is ~90MB, runs on CPU, and generates 384-dim vectors in ~5ms. No GPU required.

---

### Part 9 — Geo + Search Fusion

#### [MODIFY] `search_service/main.py`
- Fused `/search/properties` endpoint incorporates:
  - PostgreSQL FTS relevance score (`ts_rank`)
  - PostGIS `ST_Distance` proximity score
  - Locality score from `geo_amenity.locality_scores`
  - Commute score from `geo_amenity.commute_matrix`
  - Behavioral popularity from Redis `search:popular:*`
  - Ranking engine final score
- All scores normalized to 0-1 before weighted combination

---

### Part 10 — Redis Performance Optimization

#### [MODIFY] `shared_redis.py`
Add new key helpers:
- `get_search_results_key(query_hash)` → `search:results:{hash}` (3 min TTL)
- `get_autocomplete_key(prefix)` → `search:autocomplete:{prefix}` (5 min TTL)
- `get_trending_key()` → `search:trending` (sorted set)
- `get_popular_property_key(id)` → `search:popular:{id}` (sorted set member)
- `get_recommendation_key(user_id)` → `rec:user:{user_id}` (30 min TTL)
- `get_similar_key(property_id)` → `rec:similar:{property_id}` (1 hr TTL)

Cache invalidation: on `property_updated`, flush related result/recommendation keys.

---

### Part 11 — Gateway & Docker Integration

#### [MODIFY] `gateway/main.py`
- Add `/search/*` → `search_service` (port 8015) route
- Add search_service to diagnostics registry

#### [MODIFY] `docker-compose.yml`
- Add `search_service` container (port 8015)
- Add OpenSearch single-node container (port 9200) — **optional, for future readiness**

#### [MODIFY] `requirements.txt`
- Add `opensearch-py`, `sentence-transformers`, `pgvector`, `scikit-learn`

---

### Part 12 — Frontend Discovery UX

#### [MODIFY] `frontend/src/components/HeroSearch.tsx`
- Add trending searches below search bar
- Add contextual suggestion chips: "Near Manyata Tech Park", "Family-friendly", "Near Metro"
- Animate suggestion dropdown with ranking explanations

#### [MODIFY] `frontend/src/components/SearchBar.tsx`
- Extend suggestions with type icons (🏢 office, 🚇 metro, 🏘️ locality, 🏠 property)
- Add "Popular searches" section when input is empty

#### [MODIFY] `frontend/src/pages/Listings.tsx`
- Add infinite scroll / pagination (replace all-at-once load)
- Add "Recommended for you" section above results
- Add "Similar properties" ribbon on each card
- Add "Sorted by: Relevance" dropdown with ranking profile selector
- Add commute score / locality score filter chips
- Add map-search synchronization (when map moves → update results)
- Add ranking explanation tooltip on hover

#### [NEW] `frontend/src/api/search.ts`
- Typed API client for all search_service endpoints
- Analytics event tracking functions

#### [NEW] `frontend/src/components/RecommendationRow.tsx`
- Horizontal scroll carousel of recommended properties
- "Why recommended" tooltip per card

#### [NEW] `frontend/src/components/TrendingSearches.tsx`
- Trending search chips with navigation

---

### Part 13 — Event Architecture Extensions

New RabbitMQ routing keys (all published to `rentora_exchange`):
- `search.property_index_updated`
- `search.analytics.property_viewed`
- `search.analytics.search_performed`
- `search.analytics.contact_initiated`
- `recommendation.updated`
- `search.trending_updated`

---

### Part 14 — Security & Rate Limiting

#### [MODIFY] `search_service/main.py`
- Add per-IP rate limiting (50 autocomplete req/min, 20 search req/min) via Redis counters
- Query complexity validation (max 5 filter dimensions per request)
- Prevent deep pagination abuse (max `page` = 100, `page_size` ≤ 50)
- Sanitize geo coordinates (validate lat/lng range)

---

### Part 15 — Documentation

Save under `documents/stabilization/`:
- `implementation_plan/priority4_search_intelligence_plan.md` (this document)
- `walkthrough/priority4_search_intelligence_walkthrough.md` (post-execution)

---

## Verification Plan

### Automated Checks
```powershell
# Python syntax
venv\Scripts\python.exe -m py_compile search_service/main.py search_service/ranking_engine.py ...

# TypeScript
cd frontend; npx tsc --noEmit --skipLibCheck
```

### Functional Verification
1. `GET /search/properties?q=whitfield` → returns Whitefield results (fuzzy)
2. `GET /search/autocomplete?q=manyata` → returns "Manyata Tech Park"
3. `GET /search/trending` → returns top 10 trending searches
4. `GET /recommendations/similar/{id}` → returns 5 similar properties
5. `POST /search/track` → event stored, Redis popular score incremented
6. Gateway `/diagnostics` shows `search_service: healthy`
7. `npx tsc --noEmit` → 0 errors
