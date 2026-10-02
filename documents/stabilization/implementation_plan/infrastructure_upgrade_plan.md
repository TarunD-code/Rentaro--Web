# Implementation Plan: Rentora Priority 2 Infrastructure Upgrades

This plan details the architecture and step-by-step technical implementation to upgrade Rentora's core infrastructure from local filesystem operations and synchronous HTTP callback chains to a production-ready, distributed topology using:
1. **Centralized Object Storage** (AWS S3 / Cloudflare R2 / local dev simulation)
2. **Distributed Shared Caching & WebSocket Pub/Sub** (Redis)
3. **Asynchronous Event-Driven Messaging** (RabbitMQ topic exchange with durable DLX retries)
4. **Idempotent File Migration Suite**
5. **Unified Dockerization** for the entire microservices ensemble.

---

## 🏗️ Target Architectural Design

The new architecture decouples services and transitions them to full statelessness:

```mermaid
graph TD
    subgraph Client Layer
        Web["React Frontend"]
    end

    subgraph API Gateway Layer
        GW["API Gateway (Port 8000)"]
    end

    subgraph Messaging & Caching Layer
        Broker["RabbitMQ (Broker)"]
        Cache["Redis (Cache & Pub/Sub)"]
    end

    subgraph Stateless Microservices Ensemble
        Auth["Auth Service (8001)"]
        Profile["Profile Service (8002)"]
        Property["Property Service (8003)"]
        Payment["Payment Service (8004)"]
        Onboarding["Onboarding Service (8006)"]
        Comm["Communication Service (8007)"]
        Agreements["Agreements Service (8008)"]
        Billing["Billing Service (8009)"]
        Dashboard["Owner Dashboard (8010)"]
        Subs["Subscription Service (8011)"]
        Support["Support Service (8012)"]
        Notif["Notification Service (8013)"]
    end

    subgraph Storage & Persistence Layer
        DB[(PostgreSQL)]
        S3["S3 / R2 Object Storage"]
    end

    Web -->|HTTPS| GW
    GW -->|Reverse Proxy| Stateless-Microservices
    Stateless-Microservices --> DB
    Stateless-Microservices -->|Metadata / Blobs| S3
    Stateless-Microservices -->|Read/Write Cache| Cache
    Stateless-Microservices -->|Publish/Subscribe Events| Broker
    Comm <-->|Clustered Websockets via Redis Adapter| Web
```

---

## 🛠️ Proposed Infrastructure Modules

We will introduce three centralized root-level Python modules so they can be seamlessly loaded by all FastAPI services:

### 1. Centralized Object Storage Module (`shared_storage.py`)
Provides a standard client class that connects dynamically to any S3-compatible service using `boto3`. 
* **Fallback Mode**: If `STORAGE_PROVIDER=local` is active, it runs an internal sandbox class that simulates object storage in the local `uploads` directory and returns CDN-ready loopback URLs (retaining 100% offline development sandbox behavior).
* **Interface**:
  ```python
  def upload_file(file_obj, file_key: str, content_type: str = None) -> str
  def delete_file(file_key: str) -> bool
  def get_public_url(file_key: str) -> str
  def get_signed_url(file_key: str, expires_in: int = 3600) -> str
  def list_files(prefix: str = "") -> List[str]
  ```

### 2. Centralized Caching Module (`shared_redis.py`)
Manages standard connection pooling and exposes caching primitives:
* **Interface**:
  ```python
  def get(key: str) -> Optional[str]
  def set(key: str, value: str, ttl: int = None) -> bool
  def delete(key: str) -> bool
  def acquire_lock(lock_key: str, expire_seconds: int = 10) -> bool
  def release_lock(lock_key: str) -> bool
  ```
* **Namespace Standardization**:
  * `property:listing:<id>` (TTL: 3600s)
  * `property:search:<query_hash>` (TTL: 600s)
  * `property:locality:<score_id>` (TTL: 86400s)
  * `onboarding:state:<user_id>` (TTL: 1800s)
* **Automatic Cache Invalidation Triggers**:
  * `Property` Create/Update/Delete $\rightarrow$ Invalidate matching `property:listing:*` and search suggestions.

### 3. Centralized Event Broker Module (`shared_event_broker.py`)
Utilizes `pika` to bind all services to RabbitMQ:
* **Exchange Configuration**: Durable Topic Exchange (`rentora_exchange`).
* **Resiliency & DLX**:
  * Dead-Letter Exchange (`rentora_dlx`) and Dead-Letter Queue (`rentora_dlq`).
  * If a consumer crashes or fails to process a message after 3 retries (using exponential backoff), the message is routed to the DLQ to prevent blocking the execution pipeline.
* **Standard Event Schema**:
  ```json
  {
    "event_id": "uuid-string",
    "event_type": "property.created",
    "source_service": "property_service",
    "target_service": "notification_service",
    "timestamp": "2026-05-18T12:00:00Z",
    "payload": {},
    "version": "1.0.0"
  }
  ```

---

## 🛠️ Step-by-Step Implementation Sequence

We will implement the infrastructure layers strictly in the requested sequential order:

```mermaid
gantt
    title Infrastructure Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1
    Centralized Storage (shared_storage.py) :active, p1, 2026-05-18, 1d
    section Phase 2
    Idempotent File Migration Script       : p2, after p1, 1d
    section Phase 3
    Centralized Redis (shared_redis.py)    : p3, after p2, 1d
    Websocket Redis PubSub Integration     : p4, after p3, 1d
    section Phase 4
    RabbitMQ Broker (shared_event_broker.py): p5, after p4, 1d
    Event Refactor (deleting HTTP callbacks): p6, after p5, 1d
    section Phase 5
    Dockerization (Dockerfiles & Compose)  : p7, after p6, 1d
    E2E Verification & Observability       : p8, after p7, 1d
```

### Phase 1: Centralized Object Storage Migration
1. Create `shared_storage.py` at the root directory.
2. Refactor `profile_service/storage.py` and `property_service/media_processor.py` to route uploads through the storage layer.
3. Update `property_service/agreements.py` to generate PDF files directly in S3-compatible storage rather than the local filesystem.
4. Refactor `owner_dashboard_service/report_generator.py` and other services to utilize `shared_storage.py`.

### Phase 2: Idempotent File Migration Script
1. Create `scripts/migrate_to_storage.py`.
2. Connect to PostgreSQL using `shared_database.py`.
3. Scan all legacy database columns containing local `/static/` paths or mock-s3 stubs.
4. Upload those local files to the target storage provider.
5. Update columns with the generated keys and CDN URLs.
6. Verify file integrity using SHA-256 validation.

### Phase 3: Redis Caching Layer & WebSocket Clustered Adapter
1. Create `shared_redis.py`.
2. Refactor `property_service/main.py` search and property detail routes to check Redis first.
3. Add invalidation signals on listing creates, updates, and deletes.
4. Integrate Redis Pub/Sub adapter inside `communication_service/src/server.ts` to allow multi-instance socket clustering.

### Phase 4: RabbitMQ Event Broker & Decoupling
1. Create `shared_event_broker.py`.
2. Replace synchronous internal callbacks `/internal/events` inside `property_service` and others.
3. Boot event-consuming daemons inside services to process incoming asynchronous alerts.
4. Set up DLX queues and exponential retry backoff parameters.

### Phase 5: Observability, Health Checks, and Docker Setup
1. Expose `GET /health` indicators verifying Postgres, Redis, RabbitMQ, and Object Storage connection reachability.
2. Standardize logs to output Structured JSON including Correlation IDs tracing messages across services.
3. Create lightweight `Dockerfile` files for all 13 microservices.
4. Generate a production-grade `docker-compose.yml` exposing only the Gateway externally.

---

## 🔍 Verification Plan

### Automated Checks
* **Syntax Compilation**: Ensure all upgraded python scripts compile cleanly under uvicorn run checks.
* **Storage Upload Tests**: Assert file uploads to Local Mock/MinIO return correctly structured URLs.
* **Cache Invalidation Test**: Assert listing price changes instantly wipe out cached listings from Redis.
* **Broker Delivery Test**: Verify simulated server disconnects do not drop RabbitMQ persistent messages.

### Manual Verification
* Execute signups, listing media uploads, and generate legal agreements via the React frontend.
* Check Docker Compose internal networking to guarantee microservices cannot be accessed from port 8001-8013 externally.

---

## 🚦 User Review Required

> [!WARNING]
> To run the complete event broker, caching, and object storage suite in your developer workspace, you will need local instances of **Redis** and **RabbitMQ**. We will add resilient **fallback stubs** to ensure the code works perfectly even if these external services are temporarily offline in your development sandbox, preventing any environment startup blockers.

---

## 💬 Open Questions

1. **MinIO / Local Sandbox Endpoint**: Do you have a running MinIO or Redis server port on your local machine, or should we default our stubs to standard sandbox addresses (`localhost:6379` for Redis and `amqp://guest:guest@localhost:5672` for RabbitMQ)?
2. **R2 Endpoint Format**: Should we default the CF R2 endpoint variable to MinIO standard syntax, or construct custom URL parsing for R2 buckets?
