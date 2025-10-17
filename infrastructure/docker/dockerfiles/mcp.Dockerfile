# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI MCP SERVER DOCKERFILE
# ============================================
# Multi-stage build optimized for Model Context Protocol
# Security-first approach with Python 3.12
# Updated: 2025-09-25
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
        tini \
        git && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user with specific UID/GID for MCP
    groupadd -r -g 1003 mcp && \
    useradd -r -u 1003 -g mcp -d /app -s /sbin/nologin mcp && \
    mkdir -p /app /data/contexts /data/agents && \
    chown -R mcp:mcp /app /data

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
        libffi-dev \
        libssl-dev \
        build-essential && \
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
    # Install MCP-specific packages
    pip install --no-deps \
        websockets==12.0 \
        asyncio-mqtt==0.16.2 \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        pydantic==2.5.0 \
        redis==5.0.1 \
        psycopg[binary]==3.1.12 && \
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
        git \
        vim \
        procps \
        htop \
        jq && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install development dependencies
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --no-deps \
        ipython \
        ipdb \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        isort \
        mypy \
        ruff \
        debugpy

# Copy application code (will be overridden by volume mount)
COPY --chown=mcp:mcp . .

# Switch to non-root user
USER mcp

# Development command with hot reload
CMD ["python", "-m", "core.mcp.server", "--reload", "--debug"]

# ============================================
# PRODUCTION STAGE - Minimal production image
# ============================================
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder --chown=mcp:mcp /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=mcp:mcp core ./core
COPY --chown=mcp:mcp database ./database
COPY --chown=mcp:mcp toolboxai_settings ./toolboxai_settings

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /data/contexts /data/agents /tmp/mcp && \
    chown -R mcp:mcp /app/logs /data/contexts /data/agents /tmp/mcp && \
    chmod 755 /app/logs /data/contexts /data/agents /tmp/mcp

# MCP Server environment variables
ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=9877 \
    LOG_LEVEL=info \
    MAX_TOKENS=8192 \
    AGENT_DISCOVERY_ENABLED=true \
    MAX_CONCURRENT_CONNECTIONS=100 \
    WEBSOCKET_PING_INTERVAL=20 \
    WEBSOCKET_PING_TIMEOUT=10 \
    CONTEXT_CACHE_SIZE=1000 \
    AGENT_TIMEOUT=300

# Create health check script with echo commands
RUN echo '#!/usr/bin/env python3' > /app/healthcheck.py && \
    echo 'import sys' >> /app/healthcheck.py && \
    echo 'import time' >> /app/healthcheck.py && \
    echo 'import requests' >> /app/healthcheck.py && \
    echo 'try:' >> /app/healthcheck.py && \
    echo '    response = requests.get("http://localhost:9877/health", timeout=5)' >> /app/healthcheck.py && \
    echo '    if response.status_code == 200:' >> /app/healthcheck.py && \
    echo '        print("✅ MCP Server is healthy")' >> /app/healthcheck.py && \
    echo '        sys.exit(0)' >> /app/healthcheck.py && \
    echo '    else:' >> /app/healthcheck.py && \
    echo '        sys.exit(1)' >> /app/healthcheck.py && \
    echo 'except Exception as e:' >> /app/healthcheck.py && \
    echo '    print(f"❌ Health check failed: {e}")' >> /app/healthcheck.py && \
    echo '    sys.exit(1)' >> /app/healthcheck.py

RUN chmod +x /app/healthcheck.py

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI MCP Server" \
      org.opencontainers.image.description="Model Context Protocol server for AI agent coordination" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-09-25" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      org.opencontainers.image.documentation="https://docs.toolboxai.solutions" \
      org.opencontainers.image.licenses="MIT"

# Security: Set filesystem to read-only (writable directories via tmpfs in compose)
RUN chmod -R a-w /app && \
    chmod -R u+w /app/logs /data/contexts /data/agents /tmp/mcp

# Switch to non-root user
USER mcp

# Expose MCP server port
EXPOSE 9877

# Health check using custom script
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Production command with optimized settings
CMD ["python", "-m", "core.mcp.server", \
     "--host", "0.0.0.0", \
     "--port", "9877", \
     "--log-level", "info", \
     "--max-connections", "100", \
     "--enable-compression", \
     "--enable-extensions"]
