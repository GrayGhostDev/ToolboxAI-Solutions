# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI CELERY WORKER DOCKERFILE
# ============================================
# Multi-stage build for Celery background task workers
# Implements security best practices and BuildKit features
# Updated: 2025-09-26
# ============================================

# ============================================
# BASE STAGE - Common dependencies
# ============================================
FROM python:3.12-slim AS base

# Install security updates and runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        netcat-traditional \
        tini \
        # Additional dependencies for Celery
        libpq5 \
        libxml2 \
        libxslt1.1 && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user for Celery worker
    groupadd -r -g 1005 celery && \
    useradd -r -u 1005 -g celery -d /app -s /sbin/nologin celery && \
    mkdir -p /app /app/logs /app/data && \
    chown -R celery:celery /app

# Set working directory
WORKDIR /app

# Python environment variables optimized for Celery
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # Celery specific
    C_FORCE_ROOT=false \
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=true

# ============================================
# BUILDER STAGE - Build dependencies
# ============================================
FROM base AS builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt requirements-celery.txt* ./
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip setuptools wheel && \
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt && \
    # Install Celery and related packages
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org \
        celery[redis,msgpack]==5.3.* \
        flower==2.0.* \
        celery-redbeat==2.1.* \
        celery-singleton==0.3.* \
        kombu==5.3.* \
        vine==5.1.* \
        billiard==4.2.* \
        # Monitoring and metrics
        prometheus-client==0.19.* \
        py-spy==0.3.* \
        # Task result backends
        sqlalchemy==2.0.* \
        psycopg2-binary==2.9.* && \
    # Install additional requirements if exists
    if [ -f requirements-celery.txt ]; then pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements-celery.txt; fi

# ============================================
# DEVELOPMENT STAGE
# ============================================
FROM base AS development

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install development tools
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        vim \
        less \
        procps \
        htop && \
    rm -rf /var/lib/apt/lists/*

# Copy application code (will be overridden by volume mount in dev)
COPY --chown=celery:celery . /app

# Development environment variables
ENV CELERY_TASK_ALWAYS_EAGER=false \
    CELERY_TASK_EAGER_PROPAGATES=false \
    CELERY_SEND_TASK_EVENTS=true \
    CELERY_SEND_EVENTS=true \
    FLOWER_DEBUG=true

# Create directories for Celery
RUN mkdir -p /app/celery /app/logs /app/data /var/run/celery /var/log/celery && \
    chown -R celery:celery /app /var/run/celery /var/log/celery

# Switch to non-root user
USER celery

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A apps.backend.celery_app inspect ping -d celery@$HOSTNAME || exit 1

# Development entrypoint with hot reload
ENTRYPOINT ["tini", "--"]
CMD ["celery", "-A", "apps.backend.celery_app", "worker", \
     "--loglevel=DEBUG", \
     "--concurrency=2", \
     "--pool=prefork", \
     "--task-events", \
     "--without-heartbeat", \
     "--without-gossip", \
     "--without-mingle", \
     "--max-tasks-per-child=100", \
     "--autoscale=4,1", \
     "-Q", "default,high_priority,low_priority"]

# ============================================
# PRODUCTION STAGE
# ============================================
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=celery:celery apps /app/apps
COPY --chown=celery:celery core /app/core
COPY --chown=celery:celery database /app/database
COPY --chown=celery:celery toolboxai_settings /app/toolboxai_settings

# Production optimizations
ENV CELERY_OPTIMIZATION=fair \
    CELERY_PREFETCH_MULTIPLIER=4 \
    CELERY_MAX_TASKS_PER_CHILD=1000 \
    CELERY_TASK_COMPRESSION=gzip \
    CELERY_RESULT_COMPRESSION=gzip \
    CELERY_MESSAGE_COMPRESSION=gzip \
    CELERY_TASK_TIME_LIMIT=300 \
    CELERY_TASK_SOFT_TIME_LIMIT=240 \
    CELERY_WORKER_HIJACKING_TIMEOUT=300 \
    CELERY_WORKER_DISABLE_RATE_LIMITS=false

# Create necessary directories with proper permissions
RUN mkdir -p /var/run/celery /var/log/celery /tmp/celery && \
    chown -R celery:celery /var/run/celery /var/log/celery /tmp/celery && \
    chmod 755 /var/run/celery /var/log/celery /tmp/celery

# Security hardening
USER celery

# Production health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD celery -A apps.backend.celery_app inspect ping -d celery@$HOSTNAME || exit 1

# Production entrypoint
ENTRYPOINT ["tini", "--"]
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
