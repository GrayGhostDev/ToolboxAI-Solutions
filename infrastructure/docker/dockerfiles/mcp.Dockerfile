# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI MCP SERVER DOCKERFILE
# ============================================
# Multi-stage build optimized for Model Context Protocol
# Security-first approach with Python 3.12
# Updated: 2025-09-25
# ============================================

# ============================================
# BASE STAGE - Use backend image with all dependencies
# ============================================
# Backend image already has tiktoken==0.12.0 and all Python dependencies
# Backend runs as user 'toolboxai' (UID 1001) - we'll reuse this user
FROM toolboxai/backend:latest AS base

# Switch to root temporarily to create MCP directories
USER root

# Create MCP-specific directories (reuse existing toolboxai user from backend)
RUN mkdir -p /data/contexts /data/agents && \
    chown -R toolboxai:toolboxai /data

# Set working directory
WORKDIR /app

# MCP-specific environment variables (inherit Python vars from backend)
ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=9877 \
    LOG_LEVEL=info

# ============================================
# BUILDER STAGE - Skipped (using backend deps)
# ============================================
# All dependencies already installed in backend image

# ============================================
# DEVELOPMENT STAGE - For local development
# ============================================
FROM base AS development

# Install dev tools (git, vim, etc. already in backend image)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        jq && \
    rm -rf /var/lib/apt/lists/*

# Virtual environment already present from backend image at /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Development dependencies already installed in backend image
# (ipython, ipdb, pytest, black, etc.)

# Copy application code (will be overridden by volume mount)
COPY --chown=toolboxai:toolboxai . .

# Switch to non-root user (reuse toolboxai from backend)
USER toolboxai

# Development command with hot reload
CMD ["python", "-m", "core.mcp.server", "--reload", "--debug"]

# ============================================
# PRODUCTION STAGE - Minimal production image
# ============================================
FROM base AS production

# Virtual environment already present from backend image
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=toolboxai:toolboxai core ./core
COPY --chown=toolboxai:toolboxai database ./database
COPY --chown=toolboxai:toolboxai toolboxai_settings ./toolboxai_settings

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /data/contexts /data/agents /tmp/mcp && \
    chown -R toolboxai:toolboxai /app/logs /data/contexts /data/agents /tmp/mcp && \
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

# Switch to non-root user (reuse toolboxai from backend)
USER toolboxai

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