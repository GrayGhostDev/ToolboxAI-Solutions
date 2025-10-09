# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI BACKEND DOCKERFILE
# ============================================
# Multi-stage build optimized for Docker Engine 25.x
# Implements security best practices and BuildKit features
# Updated: 2025-09-24
# ============================================

# ============================================
# BASE STAGE - Common dependencies
# ============================================
FROM python:3.12-slim AS base

# Install security updates and common dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        netcat-traditional \
        tini && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user with specific UID/GID
    groupadd -r -g 1001 toolboxai && \
    useradd -r -u 1001 -g toolboxai -d /app -s /sbin/nologin toolboxai && \
    mkdir -p /app && \
    chown -R toolboxai:toolboxai /app

# Set working directory
WORKDIR /app

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ROOT_USER_ACTION=ignore

# ============================================
# BUILDER STAGE - Build dependencies
# ============================================
FROM base AS builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libpq-dev \
        libffi-dev \
        libssl-dev \
        git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-ai.txt* ./

# Install Python dependencies with cache mount
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
    # Clean up pip cache
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete 2>/dev/null || true

# ============================================
# DEVELOPMENT STAGE - For local development
# ============================================
FROM base AS development

# Install dev tools
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libpq-dev \
        git \
        vim \
        procps \
        htop && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install development dependencies
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --no-deps --trusted-host pypi.org --trusted-host files.pythonhosted.org \
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

# Copy application code (will be overridden by volume mount)
COPY --chown=toolboxai:toolboxai . .

# Switch to non-root user
USER toolboxai

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", \
     "--host", "0.0.0.0", "--port", "8009", "--reload", \
     "--reload-dir", "/app", "--log-level", "debug"]

# ============================================
# PRODUCTION STAGE - Minimal production image
# ============================================
FROM base AS production

# Install only runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get autoremove -y

# Copy virtual environment from builder
COPY --from=builder --chown=toolboxai:toolboxai /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=toolboxai:toolboxai apps/backend ./apps/backend
COPY --chown=toolboxai:toolboxai core ./core
COPY --chown=toolboxai:toolboxai database ./database
COPY --chown=toolboxai:toolboxai toolboxai_settings ./toolboxai_settings
COPY --chown=toolboxai:toolboxai toolboxai_utils ./toolboxai_utils

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/agent_data /app/memory_store /tmp/app && \
    chown -R toolboxai:toolboxai /app/logs /app/agent_data /app/memory_store /tmp/app && \
    chmod 755 /app/logs /app/agent_data /app/memory_store /tmp/app

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Backend" \
      org.opencontainers.image.description="FastAPI backend with AI agents and MCP" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-09-24" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      org.opencontainers.image.documentation="https://docs.toolboxai.solutions" \
      org.opencontainers.image.licenses="MIT"

# Security: Set filesystem to read-only (writable directories via tmpfs in compose)
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
ENTRYPOINT ["/usr/bin/tini", "--"]

# Production command with uvloop for better performance
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", \
     "--host", "0.0.0.0", "--port", "8009", \
     "--workers", "4", "--loop", "uvloop", \
     "--access-log", "--log-level", "warning", \
     "--timeout-keep-alive", "75", \
     "--limit-concurrency", "1000", \
     "--limit-max-requests", "10000", \
     "--timeout-graceful-shutdown", "30"]

# ============================================
# DISTROLESS STAGE - Ultra-minimal production (optional)
# ============================================
FROM gcr.io/distroless/python3-debian12:nonroot AS distroless

# Copy Python environment and application
COPY --from=production /opt/venv /opt/venv
COPY --from=production --chown=nonroot:nonroot /app /app

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app
EXPOSE 8009

# Note: Distroless doesn't have shell, so health checks must be external
ENTRYPOINT ["python", "-m", "uvicorn", "apps.backend.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8009", "--workers", "4"]