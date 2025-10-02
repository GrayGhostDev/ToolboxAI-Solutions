# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI CELERY WORKERS - OPTIMIZED
# ============================================
# Ultra-optimized multi-stage build with Alpine
# Target: <200MB per worker image
# Builds: Worker, Beat, Flower, Exporter
# Docker Engine 25.x with BuildKit
# Created: 2025-10-02
# ============================================

# ============================================
# BUILDER STAGE - Dependencies compilation
# ============================================
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add --no-cache \
        gcc \
        musl-dev \
        postgresql-dev \
        libffi-dev \
        g++ \
        make

# Set working directory
WORKDIR /build

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements files
COPY requirements.txt ./

# Create virtual environment and install dependencies
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -r requirements.txt && \
    # Install Celery monitoring dependencies
    pip install --no-deps \
        prometheus-client==0.20.0 \
        psutil==5.9.8 \
        flower==2.0.1 \
        celery-prometheus-exporter==1.8.0 && \
    # Clean up
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyo" -delete 2>/dev/null || true && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# ============================================
# BASE RUNTIME STAGE - Common configuration
# ============================================
FROM python:3.12-alpine AS base

# Install only runtime dependencies
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add --no-cache \
        postgresql-libs \
        libffi \
        curl \
        tini \
        ca-certificates && \
    # Create celery user
    addgroup -g 1003 celery && \
    adduser -D -u 1003 -G celery -h /app -s /sbin/nologin celery && \
    # Create necessary directories
    mkdir -p /app /var/log/celery /tmp/app /app/celerybeat-schedule && \
    chown -R celery:celery /app /var/log/celery /tmp/app /app/celerybeat-schedule

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    PIP_NO_CACHE_DIR=1

# Copy virtual environment from builder
COPY --from=builder --chown=celery:celery /opt/venv /opt/venv

# Copy application code
COPY --chown=celery:celery apps/backend/ ./apps/backend/
COPY --chown=celery:celery toolboxai_settings/ ./toolboxai_settings/

# ============================================
# WORKER STAGE - Celery Worker
# ============================================
FROM base AS worker

# Switch to non-root user
USER celery

# Add metadata
LABEL org.opencontainers.image.title="ToolBoxAI Celery Worker (Optimized)" \
      org.opencontainers.image.description="Celery worker for background tasks - Alpine optimized <200MB" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-10-02" \
      org.opencontainers.image.base.name="python:3.12-alpine"

# Health check for worker
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD celery -A apps.backend.workers.celery_app inspect ping || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Default command
CMD ["celery", "-A", "apps.backend.workers.celery_app", "worker", \
     "--loglevel=INFO", "--concurrency=4", "--pool=prefork"]

# ============================================
# BEAT STAGE - Celery Beat Scheduler
# ============================================
FROM base AS beat

# Switch to non-root user
USER celery

# Add metadata
LABEL org.opencontainers.image.title="ToolBoxAI Celery Beat (Optimized)" \
      org.opencontainers.image.description="Celery beat scheduler - Alpine optimized <150MB" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-10-02"

# Health check for beat
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "celery.*beat" || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Default command
CMD ["celery", "-A", "apps.backend.workers.celery_app", "beat", \
     "--loglevel=INFO", "--schedule=/app/celerybeat-schedule/celerybeat-schedule.db"]

# ============================================
# FLOWER STAGE - Monitoring Dashboard
# ============================================
FROM base AS flower

# Create flower user
USER root
RUN adduser -D -u 1004 -h /app flower && \
    chown -R flower:flower /app

# Switch to flower user
USER flower

# Add metadata
LABEL org.opencontainers.image.title="ToolBoxAI Flower (Optimized)" \
      org.opencontainers.image.description="Celery monitoring dashboard - Alpine optimized <200MB" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-10-02"

# Expose Flower port
EXPOSE 5555

# Health check for Flower
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5555/api/workers || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Default command
CMD ["celery", "-A", "apps.backend.workers.celery_app", "flower", \
     "--port=5555", "--basic_auth=admin:password"]

# ============================================
# EXPORTER STAGE - Prometheus Metrics
# ============================================
FROM base AS exporter

# Create exporter user
USER root
RUN adduser -D -u 1005 -h /app exporter && \
    chown -R exporter:exporter /app

# Copy monitoring scripts if they exist
COPY --chown=exporter:exporter apps/backend/workers/monitoring/ ./apps/backend/workers/monitoring/ 2>/dev/null || true

# Switch to exporter user
USER exporter

# Add metadata
LABEL org.opencontainers.image.title="ToolBoxAI Celery Exporter (Optimized)" \
      org.opencontainers.image.description="Prometheus metrics exporter - Alpine optimized <150MB" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-10-02"

# Expose metrics port
EXPOSE 9540

# Health check for exporter
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:9540/metrics || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Default command
CMD ["python", "-m", "apps.backend.workers.monitoring.celery_exporter", \
     "--port=9540", "--interval=15"]

# ============================================
# DEVELOPMENT STAGE - Hot reload support
# ============================================
FROM base AS development

# Switch back to root for installing dev tools
USER root

# Install development tools
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add --no-cache \
        gcc \
        musl-dev \
        postgresql-dev \
        vim \
        htop \
        bash

# Install development dependencies
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    . /opt/venv/bin/activate && \
    pip install --no-deps \
        watchdog[watchmedo]==4.0.0 \
        celery[debug]==5.4.0 \
        ipdb==0.13.13

# Switch back to celery user
USER celery

# Add metadata
LABEL org.opencontainers.image.title="ToolBoxAI Celery Development" \
      org.opencontainers.image.description="Development worker with hot reload"

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Development command with hot reload
CMD ["watchmedo", "auto-restart", "--directory=/app", "--pattern=*.py", \
     "--recursive", "--", "celery", "-A", "apps.backend.workers.celery_app", \
     "worker", "--loglevel=DEBUG", "--concurrency=2", "--pool=solo"]
