# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI BASE DOCKERFILE
# ============================================
# Shared base image for all ToolBoxAI services
# Optimized for security and performance
# Updated: 2025-09-26
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
        tini \
        libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get autoremove -y

# Create non-root user for security
RUN groupadd -r -g 1001 toolboxai && \
    useradd -r -u 1001 -g toolboxai -d /app -s /sbin/nologin toolboxai && \
    mkdir -p /app && \
    chown -R toolboxai:toolboxai /app

WORKDIR /app

# Set common environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ROOT_USER_ACTION=ignore \
    TZ=UTC

# Common Python dependencies builder stage
FROM base AS python-builder

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

# Copy and install base requirements
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -r requirements.txt && \
    # Install common security packages
    pip install --no-deps \
        PyJWT==2.10.1 \
        python-jose[cryptography]==3.3.0 \
        httpx==0.27.0 \
        cryptography==43.0.3 && \
    # Clean up
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete 2>/dev/null || true

# ============================================
# RUNTIME BASE - For production services
# ============================================
FROM base AS runtime

# Copy virtual environment from builder
COPY --from=python-builder --chown=toolboxai:toolboxai /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create standard directories
RUN mkdir -p /app/logs /app/data /tmp/app && \
    chown -R toolboxai:toolboxai /app/logs /app/data /tmp/app && \
    chmod 755 /app/logs /app/data /tmp/app

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Base" \
      org.opencontainers.image.description="Base image for ToolBoxAI services" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-09-26" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      org.opencontainers.image.licenses="MIT"

# Switch to non-root user
USER toolboxai

# Use tini as entrypoint for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]