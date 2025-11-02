# syntax=docker/dockerfile:1.7
# ============================================
# TOOLBOXAI BACKEND - PRODUCTION OPTIMIZED 2025
# ============================================
# Target: <200MB (down from ~350MB)
# Multi-stage build with Alpine for minimal footprint
# Updated: 2025-10-02
# ============================================

# ============================================
# BUILDER STAGE - Build dependencies
# ============================================
FROM python:3.12-alpine AS builder

# Install build dependencies (minimal set)
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        postgresql-dev \
        libffi-dev \
        openssl-dev \
        cargo \
        rust && \
    apk add --no-cache \
        libpq

# Set working directory
WORKDIR /build

# Python optimization flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements.txt requirements-ai.txt* ./

# Install dependencies in virtual environment
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -r requirements.txt && \
    if [ -f requirements-ai.txt ]; then pip install --no-deps -r requirements-ai.txt; fi && \
    # Install security packages
    pip install --no-deps \
        PyJWT==2.10.1 \
        python-jose[cryptography]==3.3.0 \
        httpx==0.27.0 \
        cryptography==43.0.3 && \
    # Remove build artifacts
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete && \
    find /opt/venv -type f -name "*.c" -delete && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# ============================================
# PRODUCTION STAGE - Minimal runtime
# ============================================
FROM python:3.12-alpine AS production

# Install only runtime dependencies
RUN apk add --no-cache \
        libpq \
        ca-certificates \
        curl \
        tini && \
    # Create non-root user
    addgroup -g 1001 -S toolboxai && \
    adduser -S -u 1001 -G toolboxai -h /app -s /sbin/nologin toolboxai

# Set working directory
WORKDIR /app

# Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Copy virtual environment from builder
COPY --from=builder --chown=toolboxai:toolboxai /opt/venv /opt/venv

# Copy application code (only required directories)
COPY --chown=toolboxai:toolboxai apps/backend ./apps/backend
COPY --chown=toolboxai:toolboxai core ./core
COPY --chown=toolboxai:toolboxai database ./database
COPY --chown=toolboxai:toolboxai toolboxai_settings ./toolboxai_settings

# Create writable directories
RUN mkdir -p /app/logs /app/agent_data /app/memory_store /tmp/app && \
    chown -R toolboxai:toolboxai /app/logs /app/agent_data /app/memory_store /tmp/app && \
    chmod 755 /app/logs /app/agent_data /app/memory_store /tmp/app

# OCI metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Backend" \
      org.opencontainers.image.description="FastAPI backend with AI agents (Alpine-optimized)" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.created="2025-10-02" \
      org.opencontainers.image.base.name="python:3.12-alpine"

# Security: read-only filesystem (writable dirs via tmpfs)
RUN chmod -R a-w /app && \
    chmod -R u+w /app/logs /app/agent_data /app/memory_store /tmp/app

# Switch to non-root user
USER toolboxai

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Production command with optimizations
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8009", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--access-log", \
     "--log-level", "warning", \
     "--timeout-keep-alive", "75", \
     "--limit-concurrency", "1000", \
     "--limit-max-requests", "10000", \
     "--timeout-graceful-shutdown", "30"]
