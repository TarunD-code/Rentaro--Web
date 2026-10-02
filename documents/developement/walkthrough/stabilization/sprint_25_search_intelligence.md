# Walkthrough: Priority 4 — Search, Discovery & Recommendation Intelligence

## Executive Summary
We have successfully implemented the backend and frontend foundations for Rentora's intelligent search, discovery, and recommendation platform. This upgrade moves Rentora away from basic text-matching into an event-driven, ML-ready intelligent engine powered by PostgreSQL Full-Text Search (FTS), `pg_trgm`, `pgvector`, Redis caching, and RabbitMQ event streaming.

---

## Technical Accomplishments

### 1. New Search Infrastructure (`search_service`)
- **FTS & Semantic Setup**: Initialized PostgreSQL with `pg_trgm` (trigram fuzzy matching) and `pgvector` (semantic search readiness). Added `tsvector` indexed columns for fast text retrieval.
- **Microservice Creation**: Built a standalone `search_service` (port 8015) using FastAPI.
- **Intelligent Ranking Engine**: Implemented `ranking_engine.py` which computes a composite score (`final_score`) using 8 distinct signals:
  - Text Relevance
  - Locality & Commute Scores
  - Freshness
  - User Engagement (views, contacts)
  - Media Quality & Owner Quality
- **Ranking Profiles**: Users can now sort by intelligent profiles like *Family Friendly*, *Student/Budget*, *IT Professional*, and *Luxury/Premium*, which dynamically adjust the weighting of the 8 signals.

### 2. Behavioral Analytics Pipeline
- **Event Streaming**: Configured `property_service` to publish RabbitMQ events for property views, searches, and interactions.
- **Analytics Worker**: Built `analytics_worker.py` (a RabbitMQ consumer) to process incoming tracking events, batch them into PostgreSQL, and instantly update Redis popularity counters (`search:popular:ID`).
- **Locality Affinity**: Analytics engine now extracts a user's most searched localities to personalize future recommendations.

### 3. Autocomplete & Contextual Suggestions
- **Multi-tier Autocomplete**: Created a 4-tier suggestion pipeline:
  1. Exact prefix matching (`autocomplete_index`)
  2. Fuzzy trigram matching
  3. Live property name matching
  4. User search history
- **Trending Engine**: Connected searches to a Redis Sorted Set (`search:trending`) to calculate and serve real-time trending queries.

### 4. Recommendation Systems
Implemented multiple recommendation strategies via `/recommendations` API endpoints:
- **Similar Properties**: Content-based matching by price band, property type, and locality score.
- **For You**: Personalized recommendations based on user search history locality affinity.
- **Trending in Locality**: Popular properties near a given area.
- **People Also Viewed**: Collaborative filtering using session co-view analysis from analytics events.

### 5. Frontend Integration
- **Gateway**: Registered `search_service` in `gateway/main.py` routing `/search` and `/recommendations` paths.
- **HeroSearch.tsx**: Hooked up the new autocomplete API for real-time smart suggestions.
- **Listings.tsx**: Migrated the property fetch call to use the new `POST /search/properties` endpoint. Added a Ranking Profile selector to UI.

---

## What Needs to be Tested
1. **Search Execution**: Open the Listings page and test the Ranking Profile selector (e.g., set to "IT Professional" and observe the change in results).
2. **Autocomplete**: Type into the Hero Search bar and verify that fuzzy matches and properties return correctly.
3. **Analytics Events**: Check the `search.analytics_events` PostgreSQL table after performing searches to ensure RabbitMQ and the worker are processing events correctly.
4. **Initialization**: The schema needs to be built on the live DB using: `python scripts/initialize_search_schema.py` and `python scripts/build_search_index.py`. Note: This must be run by you locally due to Windows execution sandbox limitations.

---

## Next Steps for Stabilization
- Run `python scripts/initialize_search_schema.py` and `python scripts/build_search_index.py` from your terminal to build the search tables, PostGIS columns, and vector indexes.
- Expand the frontend to visually display the recommendation carousels (`RecommendationRow.tsx`).
- Deploy `search_service` worker process (`python -m search_service.index_worker` and `python -m search_service.analytics_worker`) in docker-compose.
