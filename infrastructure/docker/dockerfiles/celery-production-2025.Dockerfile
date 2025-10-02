# syntax=docker/dockerfile:1.7
# ============================================
# TOOLBOXAI CELERY WORKER - PRODUCTION OPTIMIZED 2025
# ============================================
# Target: <200MB (down from ~400MB)
# Alpine-based multi-stage build for minimal footprint
# Updated: 2025-10-02
# ============================================

# ============================================
# BUILDER STAGE - Build dependencies
# ============================================
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        postgresql-dev \
        libffi-dev \
        openssl-dev \
        libxml2-dev \
        libxslt-dev \
        cargo \
        rust && \
    apk add --no-cache \
        libpq \
        libxml2 \
        libxslt

WORKDIR /build

# Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements.txt requirements-celery.txt* ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -r requirements.txt && \
    # Install Celery stack
    pip install --no-deps \
        celery[redis,msgpack]==5.3.* \
        flower==2.0.* \
        celery-redbeat==2.1.* \
        kombu==5.3.* \
        vine==5.1.* \
        billiard==4.2.* \
        prometheus-client==0.19.* \
        sqlalchemy==2.0.* \
        psycopg2-binary==2.9.* && \
    # Install additional requirements if exists
    if [ -f requirements-celery.txt ]; then pip install --no-deps -r requirements-celery.txt; fi && \
    # Clean up
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# ============================================
# PRODUCTION STAGE - Minimal runtime
# ============================================
FROM python:3.12-alpine AS production

# Install runtime dependencies only
RUN apk add --no-cache \
        libpq \
        libxml2 \
        libxslt \
        ca-certificates \
        curl \
        tini && \
    # Create non-root user
    addgroup -g 1005 -S celery && \
    adduser -S -u 1005 -G celery -h /app celery

WORKDIR /app

# Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    C_FORCE_ROOT=false \
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=true

# Copy virtual environment
COPY --from=builder --chown=celery:celery /opt/venv /opt/venv

# Copy application code
COPY --chown=celery:celery apps /app/apps
COPY --chown=celery:celery core /app/core
COPY --chown=celery:celery database /app/database
COPY --chown=celery:celery toolboxai_settings /app/toolboxai_settings
COPY --chown=celery:celery toolboxai_utils /app/toolboxai_utils

# Production optimizations
ENV CELERY_OPTIMIZATION=fair \
    CELERY_PREFETCH_MULTIPLIER=4 \
    CELERY_MAX_TASKS_PER_CHILD=1000 \
    CELERY_TASK_COMPRESSION=gzip \
    CELERY_RESULT_COMPRESSION=gzip \
    CELERY_MESSAGE_COMPRESSION=gzip \
    CELERY_TASK_TIME_LIMIT=300 \
    CELERY_TASK_SOFT_TIME_LIMIT=240

# Create necessary directories
RUN mkdir -p /var/run/celery /var/log/celery /tmp/celery /app/logs /app/data && \
    chown -R celery:celery /var/run/celery /var/log/celery /tmp/celery /app/logs /app/data && \
    chmod 755 /var/run/celery /var/log/celery /tmp/celery /app/logs /app/data

# OCI metadata
LABEL org.opencontainers.image.title="ToolBoxAI Celery Worker" \
      org.opencontainers.image.description="Celery worker for background tasks (Alpine-optimized)" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.created="2025-10-02" \
      org.opencontainers.image.base.name="python:3.12-alpine"

# Security: non-root user
USER celery

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD celery -A apps.backend.celery_app inspect ping -d celery@$HOSTNAME || exit 1

# Use tini for signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Production command
CMD ["celery", "-A", "apps.backend.celery_app", "worker", \
     "--loglevel=INFO", \
     "--concurrency=4", \
     "--pool=prefork", \
     "--task-events", \
     "--without-heartbeat", \
     "--without-gossip", \
     "--without-mingle", \
     "--max-tasks-per-child=1000", \
     "--autoscale=8,2", \
     "--time-limit=300", \
     "--soft-time-limit=240", \
     "-Q", "default,high_priority,low_priority,email,reports,ai_generation"]
