# Implementation Plan: PostgreSQL Infrastructure Migration for Rentora

This plan outlines the architecture, stages, and steps to migrate the Rentora microservice datastores from a decentralized set of 13 SQLite databases into a unified, enterprise-grade, centralized PostgreSQL engine.

---

## 🎯 Goal Description

Replace 13 local, file-locked SQLite databases with a unified **PostgreSQL** datastore. The target state will support multi-schema domain separation, async connection pooling, custom schema indices, dynamic environment variables, a PostGIS-ready foundation, and a robust ETL migration script to preserve all seeded and production data (users, properties, payments, etc.) without disrupting current frontend API integrations.

---

## 🏗️ Target Architecture Overview

To achieve production-grade database isolation within a single PostgreSQL instance, we will utilize **PostgreSQL Schemas**:

```
                                  +---------------------------+
                                  |    PostgreSQL Instance    |
                                  |     Database: rentora     |
                                  +-------------+-------------+
                                                |
        +------------------+--------------------+------------------+------------------+
        |                  |                    |                  |                  |
   schema: auth     schema: property     schema: payment    schema: profile     schema: support
  - users table    - properties table   - transactions     - profiles table    - tickets table
```

Each FastAPI service will use its own schema scope, preventing table collision and enforcing strong boundaries while sharing a single pool of database connections.

---

## 🛠️ Proposed Changes

We will execute the migration sequentially across six phases:

### Phase 1: Environment & Base Configuration Setup
1. **Install PostgreSQL drivers**: Done (installed `asyncpg`, `psycopg2-binary`, and `alembic` successfully).
2. **Environment Variable Configuration**:
   - Create `.env` and `.env.example` in the root.
   - Define variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `MAPTILER_KEY`, `TWILIO_ACCOUNT_SID`, etc.
   - Standardize all 13 services to load configs dynamically using `os.environ` or Pydantic `BaseSettings`.

### Phase 2: Centralized Async Database Layer
1. **Centralized Engine & Connection Pool**:
   - Create a shared database connector mapping connection pools using `asyncpg`.
   - Setup separate `schema` parameters for each microservice metadata.
2. **FastAPI Dependencies**:
   - Update `get_db` in each database configuration to return a PostgreSQL-compatible async/sync Session.

### Phase 3: Model Refactoring & Alembic Schema Migration
1. **Convert SQLite Models to PostgreSQL**:
   - Update integer/float types to standard Postgres types (`DECIMAL`, `JSON`, `VARCHAR`, `TIMESTAMP`).
   - Add specialized indices for critical lookup queries (e.g., `user_identifier` index in `auth` schema, `owner_id`/`tenant_id` indexes in `payment` schema).
2. **PostGIS Foundation Setup**:
   - Enable the `postgis` extension on database startup.
   - Prepare properties tables in `property_service` with lat/lng geometry fields using SQLAlchemy / GeoAlchemy format foundations.
3. **Alembic Multi-Schema Engine**:
   - Create a unified `alembic` setup to automatically generate and run multi-schema migrations.

### Phase 4: ETL Data Migration Engine
1. **Build `sqlite_to_postgres.py`**:
   - Write a comprehensive ETL python script that:
     1. Automatically opens all 13 SQLite databases.
     2. Maps and converts relational SQLite table records into the corresponding PostgreSQL schema tables.
     3. Preserves exact Primary Key and Foreign Key relations.
     4. Corrects variable type transformations.
2. **Integrity Validation Suite**:
   - Count matching row assertions.
   - Verify Foreign Key compliance.

### Phase 5: Service Refactoring & SQLite Elimination
1. **Replace Session Layers**:
   - Refactor `main.py` and `database.py` across all FastAPI services to use the new connection string and session loaders.
2. **Remove SQLite Boot Hooks**:
   - Eliminate `Base.metadata.create_all()` startup hacks and replace them with a consolidated migration verification check.
3. **Refactor Express Service**:
   - Update `communication_service` to connect to PostgreSQL (schema `communication`) using standard `pg` pool library instead of local SQLite.

### Phase 6: E2E Verification & Diagnostics
1. **Gateway Diagnostic Tool Updates**:
   - Ensure gateway `/diagnostics` monitors Postgres connection pool status and schema visibility.
2. **Functional Verification**:
   - Test sign-ups, listings retrieval, and wallet payouts.
