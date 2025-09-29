# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI DEVELOPMENT DOCKERFILE
# ============================================
# Development-focused build with hot reload
# Updated: 2025-09-26
# ============================================

FROM python:3.12-slim AS base

# Install system dependencies for development
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        netcat-traditional \
        git \
        gcc \
        g++ \
        make \
        libpq-dev \
        libffi-dev \
        libssl-dev \
        vim \
        procps \
        htop \
        fish \
        tmux && \
    rm -rf /var/lib/apt/lists/* && \
    # Create development user
    groupadd -r -g 1000 dev && \
    useradd -r -u 1000 -g dev -d /app -s /usr/bin/fish -m dev && \
    mkdir -p /app && \
    chown -R dev:dev /app

WORKDIR /app

# Set Python environment variables for development
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONDEBUG=1

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-ai.txt* ./
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    if [ -f requirements-ai.txt ]; then \
        pip install -r requirements-ai.txt; \
    fi && \
    # Install development tools
    pip install \
        ipython \
        ipdb \
        pytest \
        pytest-cov \
        pytest-asyncio \
        pytest-mock \
        black \
        isort \
        mypy \
        ruff \
        debugpy \
        watchfiles \
        pre-commit \
        bandit \
        safety

# Create directories for development
RUN mkdir -p /app/logs /app/agent_data /app/memory_store /app/.pytest_cache && \
    chown -R dev:dev /app

# Copy application code (will be overridden by volume mounts in dev)
COPY --chown=dev:dev . .

# Switch to development user
USER dev

# Configure fish shell for better development experience
RUN fish -c "curl -sL https://git.io/fisher | source && fisher install jorgebucaran/fisher"

# Expose ports for debugging
EXPOSE 8009 5678 9229

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Development Environment" \
      org.opencontainers.image.description="Development container with hot reload and debugging" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-09-26"

# Development command with hot reload and debugging support
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", \
     "--host", "0.0.0.0", "--port", "8009", "--reload", \
     "--reload-dir", "/app", "--log-level", "debug", \
     "--access-log", "--use-colors"]