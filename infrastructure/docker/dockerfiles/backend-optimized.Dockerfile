# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI BACKEND DOCKERFILE - OPTIMIZED
# ============================================
# Ultra-optimized multi-stage build with Alpine
# Target: <200MB production image
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
        make \
        git

# Set working directory
WORKDIR /build

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements files
COPY requirements.txt ./
COPY requirements-ai.txt* ./

# Create virtual environment and install dependencies
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -r requirements.txt && \
    if [ -f requirements-ai.txt ]; then \
        pip install --no-deps -r requirements-ai.txt; \
    fi && \
    # Install additional security packages
    pip install --no-deps \
        PyJWT==2.10.1 \
        python-jose[cryptography]==3.3.0 \
        httpx==0.27.0 \
        cryptography==43.0.3 && \
    # Clean up
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyo" -delete 2>/dev/null || true && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "*.dist-info" -exec rm -rf {}/direct_url.json {} + 2>/dev/null || true

# ============================================
# PRODUCTION STAGE - Minimal runtime image
# ============================================
FROM python:3.12-alpine AS production

# Install only runtime dependencies
RUN --mount=type=cache,target=/var/cache/apk,sharing=locked \
    apk add --no-cache \
        postgresql-libs \
        libffi \
        curl \
        tini \
        ca-certificates && \
    # Create non-root user with specific UID/GID
    addgroup -g 1001 toolboxai && \
    adduser -D -u 1001 -G toolboxai -h /app -s /sbin/nologin toolboxai && \
    # Create necessary directories
    mkdir -p /app /tmp/app && \
    chown -R toolboxai:toolboxai /app /tmp/app

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
COPY --from=builder --chown=toolboxai:toolboxai /opt/venv /opt/venv

# Copy application code
COPY --chown=toolboxai:toolboxai apps/backend ./apps/backend
COPY --chown=toolboxai:toolboxai core ./core
COPY --chown=toolboxai:toolboxai database ./database
COPY --chown=toolboxai:toolboxai toolboxai_settings ./toolboxai_settings

# Create runtime directories with proper permissions
RUN mkdir -p /app/logs /app/agent_data /app/memory_store && \
    chown -R toolboxai:toolboxai /app/logs /app/agent_data /app/memory_store && \
    chmod 755 /app/logs /app/agent_data /app/memory_store

# Add metadata labels (OCI standard)
LABEL org.opencontainers.image.title="ToolBoxAI Backend (Optimized)" \
      org.opencontainers.image.description="FastAPI backend with AI agents - Alpine optimized <200MB" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-10-02" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      org.opencontainers.image.documentation="https://docs.toolboxai.solutions" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="python:3.12-alpine"

# Switch to non-root user
USER toolboxai

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Production command optimized for performance
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", \
     "--host", "0.0.0.0", "--port", "8009", \
     "--workers", "4", "--loop", "uvloop", \
     "--access-log", "--log-level", "warning", \
     "--timeout-keep-alive", "75", \
     "--limit-concurrency", "1000", \
     "--limit-max-requests", "10000", \
     "--timeout-graceful-shutdown", "30"]

# ============================================
# DEVELOPMENT STAGE - For local development
# ============================================
FROM production AS development

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
        ipython \
        ipdb \
        pytest \
        pytest-cov \
        pytest-asyncio \
        black \
        isort \
        mypy \
        ruff \
        debugpy

# Switch back to non-root user
USER toolboxai

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", \
     "--host", "0.0.0.0", "--port", "8009", "--reload", \
     "--reload-dir", "/app", "--log-level", "debug"]
