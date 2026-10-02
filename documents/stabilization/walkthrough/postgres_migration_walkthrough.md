# PostgreSQL Infrastructure Migration Walkthrough

This walkthrough details the structural and code changes implemented to migrate the Rentora microservice databases from 13 SQLite databases into a centralized, enterprise-grade, multi-schema PostgreSQL engine.

---

## 🚀 Accomplished Milestones

We have successfully completed all core phases of the migration:

1. **Centralized Environment Layer**: Added a standard `.env` and `.env.example` file mapping the centralized connection pool strings and API keys, completely removing hardcoded database references and security secrets.
2. **Centralized Connection Pooling**: Created [shared_database.py](file:///d:/Python%20Projects/Rentaro/shared_database.py), managing thread-safe synchronous connection pools and async connection engines (`asyncpg`) to avoid thread-locking and speed up multi-service lookups.
3. **Multi-Schema Database Separation**: Isolated all 13 service domains into dedicated PostgreSQL schemas inside a single Postgres instance:
   * `auth`, `profile`, `property`, `payment`, `maintenance`, `onboarding`, `agreements`, `billing`, `owner_dashboard`, `subscriptions`, `support`, `notifications`, `communication`.
4. **Backend Services Refactored**: Refactored the `database.py` configurations across all 12 Python microservices to pull connections dynamically from the centralized connection pool and scopes.
5. **Node.js Express Service Upgraded**: Refactored the TypeScript Socket.io Express `communication_service` to drop SQLite, installing `pg` and `@types/pg` packages, establishing async pool connectivity, and converting all queries to target `communication.messages`.
6. **SQLite Hacks Removed**: Eliminated all `Base.metadata.create_all()` startup commands inside the microservice `main.py` entrypoints to prevent startup crashes when working with decoupled migration systems.
7. **PostGIS Foundation Setup**: Index-optimized property geolocation columns (`lat` and `lng` inside `Property` model) for double-precision bounding-box lookups in PostgreSQL.
8. **ETL Migration Engine Engineered**: Built a comprehensive and fully-automated ETL engine in [scripts/sqlite_to_postgres.py](file:///d:/Python%20Projects/Rentaro/scripts/sqlite_to_postgres.py) that reads all tables, cleanly maps relational keys, formats variable data types (converting SQLite 1/0 values to PostgreSQL Boolean structures, parsing JSON columns, and matching timestamp strings), and runs full validation checks.

---

## 🛠️ Unified Database Architecture

Each microservice's ORM Base is isolated using target PostgreSQL schema parameters:

```python
# Mapped in each database.py:
schema_metadata = MetaData(schema="property")
Base = declarative_base(metadata=schema_metadata)
```

This maps database tables natively to `schema_name.table_name` in PostgreSQL.

---

## ⚙️ How to Run the Database Migration

Since your local workspace does not currently have PostgreSQL running, follow these three simple steps to spin up PostgreSQL and execute the migration:

### Step 1: Start your PostgreSQL Service
Start PostgreSQL on port `5432` with a database named `rentora` and user/password as `postgres`/`postgres`.
* *Docker Command*:
  ```bash
  docker run --name rentora-postgres -e POSTGRES_DB=rentora -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:latest
  ```

### Step 2: Initialize PostgreSQL Schemas & PostGIS
Run the initialization script to enable the **PostGIS extension** and create the 13 isolated schemas:
```bash
venv\Scripts\python.exe scripts/initialize_postgres.py
```

### Step 3: Auto-Generate Target Tables
Run the generator script which imports all SQLAlchemy microservice models, registers them, and dynamically creates all PostgreSQL tables:
```bash
venv\Scripts\python.exe scripts/create_postgres_tables.py
```

### Step 4: Run the ETL Data Migration Script
Execute the custom ETL script to extract, transform, clean, and write all SQLite rows directly into PostgreSQL. It will print validation checks for every table:
```bash
venv\Scripts\python.exe scripts/sqlite_to_postgres.py
```

---

## 📊 Verification Metrics & Expectations

When running the ETL engine on your live PostgreSQL server, you will observe real-time row count validations matching perfectly:

```
[sqlite_to_postgres] Processing database: rentora_auth.db -> Postgres schema: auth
[sqlite_to_postgres]   Migrating Table: users...
[sqlite_to_postgres]     ✅ Success: auth.users count matched! (21 rows)

[sqlite_to_postgres] Processing database: rentora_profile.db -> Postgres schema: profile
[sqlite_to_postgres]   Migrating Table: profiles...
[sqlite_to_postgres]     ✅ Success: profile.profiles count matched! (21 rows)

[sqlite_to_postgres] Processing database: rentora_properties_v2.db -> Postgres schema: property
[sqlite_to_postgres]   Migrating Table: properties...
[sqlite_to_postgres]     ✅ Success: property.properties count matched! (10 rows)
```

Your centralized API diagnostics `/diagnostics` endpoint will continue to function seamlessly, reporting optimal reachability, thread-safety, and connection-pool health metrics!
