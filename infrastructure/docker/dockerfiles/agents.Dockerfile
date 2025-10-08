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
    # Install agent-specific packages
    pip install --no-deps \
        openai==1.3.0 \
        anthropic==0.7.0 \
        langchain==0.0.350 \
        langchain-openai==0.0.2 \
        langchain-anthropic==0.0.1 \
        celery==5.3.4 \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        pydantic==2.5.0 \
        redis==5.0.1 \
        psycopg[binary]==3.1.12 \
        httpx==0.25.0 && \
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
COPY --chown=coordinator:coordinator database ./database
COPY --chown=coordinator:coordinator toolboxai_settings ./toolboxai_settings
COPY --chown=coordinator:coordinator toolboxai_utils ./toolboxai_utils

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

# Create health check script
RUN echo '#!/usr/bin/env python3' > /app/healthcheck.py && \
    echo 'import json' >> /app/healthcheck.py && \
    echo 'import sys' >> /app/healthcheck.py && \
    echo 'import time' >> /app/healthcheck.py && \
    echo 'import urllib.request' >> /app/healthcheck.py && \
    echo 'from urllib.error import URLError, HTTPError' >> /app/healthcheck.py && \
    echo '' >> /app/healthcheck.py && \
    echo 'def check_health():' >> /app/healthcheck.py && \
    echo '    """Check agent coordinator health via HTTP endpoint."""' >> /app/healthcheck.py && \
    echo '    try:' >> /app/healthcheck.py && \
    echo '        url = "http://localhost:8888/health"' >> /app/healthcheck.py && \
    echo '        with urllib.request.urlopen(url, timeout=5) as response:' >> /app/healthcheck.py && \
    echo '            if response.status == 200:' >> /app/healthcheck.py && \
    echo '                data = json.loads(response.read().decode())' >> /app/healthcheck.py && \
    echo '                status = data.get("status", "unknown")' >> /app/healthcheck.py && \
    echo '                active_agents = data.get("active_agents", 0)' >> /app/healthcheck.py && \
    echo '                queue_size = data.get("queue_size", 0)' >> /app/healthcheck.py && \
    echo '                if status == "healthy":' >> /app/healthcheck.py && \
    echo '                    print(f"✅ Agent Coordinator is healthy")' >> /app/healthcheck.py && \
    echo '                    print(f"   - Active agents: {active_agents}")' >> /app/healthcheck.py && \
    echo '                    print(f"   - Queue size: {queue_size}")' >> /app/healthcheck.py && \
    echo '                    return True' >> /app/healthcheck.py && \
    echo '                else:' >> /app/healthcheck.py && \
    echo '                    print(f"❌ Agent Coordinator unhealthy: {status}")' >> /app/healthcheck.py && \
    echo '                    return False' >> /app/healthcheck.py && \
    echo '            else:' >> /app/healthcheck.py && \
    echo '                print(f"❌ Health check failed with status: {response.status}")' >> /app/healthcheck.py && \
    echo '                return False' >> /app/healthcheck.py && \
    echo '    except (URLError, HTTPError, json.JSONDecodeError, TimeoutError) as e:' >> /app/healthcheck.py && \
    echo '        print(f"❌ Health check failed: {e}")' >> /app/healthcheck.py && \
    echo '        return False' >> /app/healthcheck.py && \
    echo '' >> /app/healthcheck.py && \
    echo 'if __name__ == "__main__":' >> /app/healthcheck.py && \
    echo '    result = check_health()' >> /app/healthcheck.py && \
    echo '    sys.exit(0 if result else 1)' >> /app/healthcheck.py

RUN chmod +x /app/healthcheck.py

# Create startup script with comprehensive logging
RUN echo '#!/bin/bash' > /app/start-coordinator.sh && \
    echo 'set -e' >> /app/start-coordinator.sh && \
    echo '' >> /app/start-coordinator.sh && \
    echo 'echo "🤖 Starting ToolBoxAI Agent Coordinator"' >> /app/start-coordinator.sh && \
    echo 'echo "📊 Configuration:"' >> /app/start-coordinator.sh && \
    echo 'echo "  - User: $(id)"' >> /app/start-coordinator.sh && \
    echo 'echo "  - Working directory: $(pwd)"' >> /app/start-coordinator.sh && \
    echo 'echo "  - Python version: $(python --version)"' >> /app/start-coordinator.sh && \
    echo 'echo "  - Max concurrent agents: ${MAX_CONCURRENT_AGENTS}"' >> /app/start-coordinator.sh && \
    echo 'echo "  - Task timeout: ${TASK_TIMEOUT}s"' >> /app/start-coordinator.sh && \
    echo 'echo "  - Queue max size: ${QUEUE_MAX_SIZE}"' >> /app/start-coordinator.sh && \
    echo '' >> /app/start-coordinator.sh && \
    echo '# Check dependencies' >> /app/start-coordinator.sh && \
    echo 'echo "🔍 Checking dependencies..."' >> /app/start-coordinator.sh && \
    echo 'python -c "import core.agents.master_orchestrator; print('✅ Agent orchestrator module available')"' >> /app/start-coordinator.sh && \
    echo 'python -c "import redis; print('✅ Redis client available')"' >> /app/start-coordinator.sh && \
    echo 'python -c "import asyncio; print('✅ Asyncio available')"' >> /app/start-coordinator.sh && \
    echo '' >> /app/start-coordinator.sh && \
    echo '# Check environment variables' >> /app/start-coordinator.sh && \
    echo 'if [ -z "$DATABASE_URL_FILE" ] && [ -z "$DATABASE_URL" ]; then' >> /app/start-coordinator.sh && \
    echo '    echo "⚠️  Warning: No database URL configured"' >> /app/start-coordinator.sh && \
    echo 'fi' >> /app/start-coordinator.sh && \
    echo '' >> /app/start-coordinator.sh && \
    echo 'if [ -z "$REDIS_URL_FILE" ] && [ -z "$REDIS_URL" ]; then' >> /app/start-coordinator.sh && \
    echo '    echo "⚠️  Warning: No Redis URL configured"' >> /app/start-coordinator.sh && \
    echo 'fi' >> /app/start-coordinator.sh && \
    echo '' >> /app/start-coordinator.sh && \
    echo '# Start the coordinator' >> /app/start-coordinator.sh && \
    echo 'echo "✅ Starting Agent Coordinator server..."' >> /app/start-coordinator.sh && \
    echo 'exec python -m core.agents.master_orchestrator \' >> /app/start-coordinator.sh && \
    echo '    --host 0.0.0.0 \' >> /app/start-coordinator.sh && \
    echo '    --port 8888 \' >> /app/start-coordinator.sh && \
    echo '    --max-workers ${MAX_CONCURRENT_AGENTS} \' >> /app/start-coordinator.sh && \
    echo '    --task-timeout ${TASK_TIMEOUT} \' >> /app/start-coordinator.sh && \
    echo '    --log-level ${LOG_LEVEL}' >> /app/start-coordinator.sh

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