# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI CELERY BEAT SCHEDULER DOCKERFILE
# ============================================
# Multi-stage build for Celery Beat periodic task scheduler
# Based on official Celery documentation best practices
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
        # Required for database connections
        libpq5 \
        # Required for timezone support
        tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user for Celery Beat
    groupadd -r -g 1006 celerybeat && \
    useradd -r -u 1006 -g celerybeat -d /app -s /sbin/nologin celerybeat && \
    mkdir -p /app /app/celerybeat-schedule && \
    chown -R celerybeat:celerybeat /app

# Set timezone to UTC (override in docker-compose if needed)
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # Celery Beat specific
    C_FORCE_ROOT=false

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
        libpq-dev \
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
    # Install Celery Beat specific packages
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org \
        celery[redis,msgpack]==5.3.* \
        celery-redbeat==2.1.* \
        django-celery-beat==2.5.* \
        cron-descriptor==1.4.* \
        python-dateutil==2.8.* \
        pytz==2024.* \
        # Database backend for schedule persistence
        sqlalchemy==2.0.* \
        psycopg2-binary==2.9.* \
        # Monitoring
        prometheus-client==0.19.* && \
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
        procps && \
    rm -rf /var/lib/apt/lists/*

# Copy application code (will be overridden by volume mount in dev)
COPY --chown=celerybeat:celerybeat . /app

# Development environment variables
ENV CELERY_BEAT_DEBUG=true \
    CELERY_BEAT_LOG_LEVEL=DEBUG \
    CELERY_BEAT_MAX_LOOP_INTERVAL=5

# Create directories for Beat schedule persistence
RUN mkdir -p /app/celerybeat-schedule /var/run/celerybeat /var/log/celerybeat && \
    chown -R celerybeat:celerybeat /app /var/run/celerybeat /var/log/celerybeat

# Switch to non-root user
USER celerybeat

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "celery.*beat" || exit 1

# Development entrypoint
ENTRYPOINT ["tini", "--"]
CMD ["celery", "-A", "apps.backend.celery_app", "beat", \
     "--loglevel=DEBUG", \
     "--scheduler", "celery.beat:PersistentScheduler", \
     "--schedule=/app/celerybeat-schedule/celerybeat-schedule.db", \
     "--pidfile=/var/run/celerybeat/celerybeat.pid"]

# ============================================
# PRODUCTION STAGE
# ============================================
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=celerybeat:celerybeat apps /app/apps
COPY --chown=celerybeat:celerybeat core /app/core
COPY --chown=celerybeat:celerybeat database /app/database
COPY --chown=celerybeat:celerybeat toolboxai_settings /app/toolboxai_settings

# Production environment variables (based on official docs)
ENV CELERY_BEAT_LOG_LEVEL=INFO \
    CELERY_BEAT_MAX_LOOP_INTERVAL=60 \
    CELERY_BEAT_SYNC_EVERY=180 \
    CELERY_BEAT_SCHEDULE_FILENAME=/app/celerybeat-schedule/celerybeat-schedule.db

# Create necessary directories with proper permissions
RUN mkdir -p /app/celerybeat-schedule /var/run/celerybeat /var/log/celerybeat && \
    chown -R celerybeat:celerybeat /app/celerybeat-schedule /var/run/celerybeat /var/log/celerybeat && \
    chmod 755 /app/celerybeat-schedule /var/run/celerybeat /var/log/celerybeat

# Security hardening
USER celerybeat

# Production health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "celery.*beat" || exit 1

# Production entrypoint - NOTE: Only one beat instance should run at a time
ENTRYPOINT ["tini", "--"]
CMD ["celery", "-A", "apps.backend.celery_app", "beat", \
     "--loglevel=INFO", \
     "--scheduler", "celery.beat:PersistentScheduler", \
     "--schedule=/app/celerybeat-schedule/celerybeat-schedule.db", \
     "--pidfile=/var/run/celerybeat/celerybeat.pid", \
     "--max-interval=60"]
