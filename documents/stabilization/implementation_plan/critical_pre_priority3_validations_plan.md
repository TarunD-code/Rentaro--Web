# Implementation Plan: Critical Pre-Priority-3 Validations

This plan outlines the system-wide stabilization changes to verify and complete the critical infrastructure layer before proceeding with future priority tasks. 

---

## 📋 Proposed Actions & Objectives

### 1. Dockerization & Service Orchestration
- **Standard Dockerfiles**: Write lightweight, parameterizable, and multi-stage `Dockerfile` templates for the Python FastAPI services and Node.js TypeScript `communication_service`.
- **Orchestrated `docker-compose.yml`**: Declare all 13 FastAPI microservices, the Gateway, PostgreSQL, Redis, and RabbitMQ with:
  - Strict start ordering using `depends_on` healthchecks.
  - Custom internal network isolation (`rentora_network`).
  - Persistent volume mounts for databases, cache dumps, and broker states.
  - Resilient restart policies.

### 2. Distributed Transaction & Event Safety
- **Redis-Backed Idempotency Engine**: Update the message consumption hook in `shared_event_broker.py` to check for processed `event_id` keys inside Redis (`event:processed:<event_id>`) with a `24h` TTL. Skip duplicate events automatically to guarantee transaction safety.
- **Durable Delivery**: Confirm that the RabbitMQ topic exchange and consumer queues remain completely durable across system restarts.

### 3. Monitoring & Management Dashboard
- **RabbitMQ Dashboard**: Configure the AMQP image `rabbitmq:3-management` and expose port `15672` inside `docker-compose.yml` to allow direct access to queues, routing pathways, and DLX backlogs.

### 4. Resilient Caching Production-Safeguards
- **Fail-Loud in Production**: Revise `shared_redis.py` connection initialization. If the environment flag `ENV=production` is active and Redis connection fails, fail loudly by throwing a fatal `ConnectionError` rather than silently degrading to the in-memory fallback.

### 5. URL Deterministic Storage Strategy
- **Standard Namespaces**: Verify that all file names, avatars, and agreement PDFs use deterministic folders and version-safe paths rather than random flat namespaces:
  - Properties: `properties/{id}/media/{uuid}.webp`
  - Agreements: `agreements/agreement_{id}.pdf`
  - Reports: `reports/report_{id}_{type}_{timestamp}.pdf`
  - Profile Avatars: `profiles/{id}/avatar.png`

### 6. Comprehensive API Gateway Health & Diagnostics
- **Deep Health Probes**: Upgrade `/diagnostics` and add `/health` to the API Gateway in `gateway/main.py` to actively probe:
  - PostgreSQL connectivity (via sync/async engines).
  - Redis ping status.
  - RabbitMQ connection status.
  - Central storage connectivity.

### 7. Correlation Tracing Engine (Request Logs)
- **Tracing Middleware**: Build a middleware inside `gateway/main.py` that intercepts all incoming requests, checks/generates a unique `X-Correlation-ID` header, and passes it downstream to all backend microservices.
- **Log Correlation**: Update microservice loggers to prepend `[Correlation-ID]` to request logs for rapid async debugging.

---

## 🛠️ Verification & Testing Plan
- Validate Docker build files and compose files.
- Compile and run checks across all modified services.
- Test endpoint parameters and error pathways.
