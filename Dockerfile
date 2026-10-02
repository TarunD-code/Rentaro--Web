# Dockerfile - Unified FastAPI service template
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user --prefer-binary torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --user --prefer-binary -r requirements.txt

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Add local path to python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Copy shared modules from root directory
COPY shared_database.py /app/shared_database.py
COPY shared_redis.py /app/shared_redis.py
COPY shared_storage.py /app/shared_storage.py
COPY shared_event_broker.py /app/shared_event_broker.py
# Environment variables are injected securely at runtime (e.g. Render / Production PaaS)
# COPY .env /app/.env

# Copy specific service directory inside container
ARG SERVICE_NAME
COPY ${SERVICE_NAME} /app/${SERVICE_NAME}

ENV SERVICE_DIR=${SERVICE_NAME}

# Default health check for FastAPI microservices
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD uvicorn ${SERVICE_DIR}.main:app --host 0.0.0.0 --port 8000
