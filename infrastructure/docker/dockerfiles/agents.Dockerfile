# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI AGENT COORDINATOR DOCKERFILE
# ============================================
# Multi-stage build optimized for AI agent orchestration
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
        procps \
        git && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user with specific UID/GID for agents
    groupadd -r -g 1004 coordinator && \
    useradd -r -u 1004 -g coordinator -d /app -s /sbin/nologin coordinator && \
    mkdir -p /app /data/agents && \
    chown -R coordinator:coordinator /app /data

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

# Install build dependencies including Rust for tiktoken
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libffi-dev \
        libssl-dev \
        build-essential \
        cargo \
        rustc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-ai.txt* ./

# Install Python dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    if [ -f requirements-ai.txt ]; then \
        pip install -r requirements-ai.txt; \
    fi && \
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
        jq \
        tree && \
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
COPY --chown=coordinator:coordinator . .

# Switch to non-root user
USER coordinator

# Development command with hot reload
CMD ["python", "-m", "core.agents.master_orchestrator", "--debug", "--reload"]

# ============================================
# PRODUCTION STAGE - Minimal production image
# ============================================
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder --chown=coordinator:coordinator /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=coordinator:coordinator core ./core
COPY --chown=coordinator:coordinator apps ./apps
COPY --chown=coordinator:coordinator database ./database
COPY --chown=coordinator:coordinator toolboxai_settings ./toolboxai_settings

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /data/agents /tmp/coordinator && \
    chown -R coordinator:coordinator /app/logs /data/agents /tmp/coordinator && \
    chmod 755 /app/logs /data/agents /tmp/coordinator

# Agent Coordinator environment variables
ENV COORDINATOR_PORT=8888 \
    LOG_LEVEL=info \
    MAX_CONCURRENT_AGENTS=10 \
    TASK_TIMEOUT=300 \
    AGENT_POOL_SIZE=5 \
    QUEUE_MAX_SIZE=1000 \
    HEARTBEAT_INTERVAL=30 \
    CLEANUP_INTERVAL=3600 \
    MEMORY_THRESHOLD=0.8 \
    CPU_THRESHOLD=0.9

# Create health check script with echo commands
RUN echo '#!/usr/bin/env python3' > /app/healthcheck.py && \
    echo 'import sys' >> /app/healthcheck.py && \
    echo 'import time' >> /app/healthcheck.py && \
    echo 'import urllib.request' >> /app/healthcheck.py && \
    echo 'try:' >> /app/healthcheck.py && \
    echo '    with urllib.request.urlopen("http://localhost:8888/health", timeout=5) as response:' >> /app/healthcheck.py && \
    echo '        if response.status == 200:' >> /app/healthcheck.py && \
    echo '            print("✅ Agent Coordinator is healthy")' >> /app/healthcheck.py && \
    echo '            sys.exit(0)' >> /app/healthcheck.py && \
    echo '        else:' >> /app/healthcheck.py && \
    echo '            sys.exit(1)' >> /app/healthcheck.py && \
    echo 'except Exception as e:' >> /app/healthcheck.py && \
    echo '    print(f"❌ Health check failed: {e}")' >> /app/healthcheck.py && \
    echo '    sys.exit(1)' >> /app/healthcheck.py

RUN chmod +x /app/healthcheck.py

# Create startup script
RUN echo '#!/bin/bash' > /app/start-coordinator.sh && \
    echo 'set -e' >> /app/start-coordinator.sh && \
    echo 'echo "🤖 Starting ToolBoxAI Agent Coordinator"' >> /app/start-coordinator.sh && \
    echo 'echo "✅ Starting Agent Coordinator server..."' >> /app/start-coordinator.sh && \
    echo 'exec python -m core.agents.master_orchestrator --host 0.0.0.0 --port 8888' >> /app/start-coordinator.sh

RUN chmod +x /app/start-coordinator.sh

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Agent Coordinator" \
      org.opencontainers.image.description="AI agent orchestration and coordination service" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-09-25" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      org.opencontainers.image.documentation="https://docs.toolboxai.solutions" \
      org.opencontainers.image.licenses="MIT"

# Security: Set filesystem to read-only (writable directories via tmpfs in compose)
RUN chmod -R a-w /app && \
    chmod -R u+w /app/logs /data/agents /tmp/coordinator && \
    chmod +x /app/start-coordinator.sh /app/healthcheck.py

# Switch to non-root user
USER coordinator

# Expose coordinator port
EXPOSE 8888

# Health check using custom script
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Production command using startup script
CMD ["/app/start-coordinator.sh"]