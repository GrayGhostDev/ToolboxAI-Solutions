# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI ROBLOX SYNC SERVICE DOCKERFILE
# ============================================
# Runs Rojo server for live-syncing Roblox Studio with filesystem
# Based on Rojo 7.4.x and Rust 1.70+ requirements
# Updated: 2025-09-26
# ============================================

# ============================================
# BASE STAGE - Rust environment for Rojo
# ============================================
# Updated to Rust 1.81 (required for rojo v7.4.1)
FROM rust:1.82-slim AS base

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        pkg-config \
        libssl-dev \
        netcat-traditional \
        tini \
        unzip && \
    rm -rf /var/lib/apt/lists/* && \
    # Create non-root user for Rojo
    groupadd -r -g 1007 rojo && \
    useradd -r -u 1007 -g rojo -d /app -s /sbin/nologin rojo && \
    mkdir -p /app /app/logs /app/projects && \
    chown -R rojo:rojo /app

# Set working directory
WORKDIR /app

# Environment variables
ENV RUST_LOG=info \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    ROJO_VERSION=7.4.1

# ============================================
# BUILDER STAGE - Build Rojo and tools
# ============================================
FROM base AS builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake && \
    rm -rf /var/lib/apt/lists/*

# Install Rojo from cargo for ARM64 compatibility
# Pre-built binaries have download issues, build from source instead
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/usr/local/cargo/git \
    cargo install rojo --version 7.4.4 --locked

# Install additional Roblox development tools
# Remove --locked flag for wildcard versions
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/usr/local/cargo/git \
    cargo install selene --version 0.26.1 && \
    cargo install stylua --version 0.20.0

# Install Rokit (Roblox toolchain manager)
RUN curl -sSf https://raw.githubusercontent.com/roblox/rokit/main/install.sh | bash

# ============================================
# DEVELOPMENT STAGE
# ============================================
FROM base AS development

# Copy built tools from builder
COPY --from=builder /usr/local/cargo/bin/rojo /usr/local/bin/rojo
COPY --from=builder /usr/local/cargo/bin/selene /usr/local/bin/selene
COPY --from=builder /usr/local/cargo/bin/stylua /usr/local/bin/stylua
COPY --from=builder /root/.rokit /opt/rokit

# Install Node.js for TypeScript support (optional)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g \
        roblox-ts@2.* \
        @rbxts/types@latest && \
    rm -rf /var/lib/apt/lists/*

# Development environment variables
ENV ROJO_DEV_MODE=true \
    ROJO_LIVE_RELOAD=true \
    ROJO_LOG_LEVEL=debug

# Create Rojo project structure
RUN mkdir -p \
    /app/src/client \
    /app/src/server \
    /app/src/shared \
    /app/src/workspace \
    /app/plugins \
    /app/assets

# Copy configuration files
COPY --chown=rojo:rojo config/rojo-config.json /app/default.project.json
COPY --chown=rojo:rojo config/selene.toml /app/selene.toml
COPY --chown=rojo:rojo config/stylua.toml /app/stylua.toml

# Switch to non-root user
USER rojo

# Health check for Rojo server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:34872/api/rojo/health || exit 1

# Development entrypoint
ENTRYPOINT ["tini", "--"]
CMD ["rojo", "serve", \
     "--address", "0.0.0.0", \
     "--port", "34872", \
     "--project", "/app/default.project.json", \
     "--verbose"]

# ============================================
# PRODUCTION STAGE
# ============================================
FROM base AS production

# Copy built tools from builder
COPY --from=builder /usr/local/cargo/bin/rojo /usr/local/bin/rojo
COPY --from=builder /usr/local/cargo/bin/selene /usr/local/bin/selene
COPY --from=builder /usr/local/cargo/bin/stylua /usr/local/bin/stylua

# Copy project files
COPY --chown=rojo:rojo roblox/src /app/src
COPY --chown=rojo:rojo roblox/plugins /app/plugins
COPY --chown=rojo:rojo roblox/assets /app/assets
COPY --chown=rojo:rojo config/rojo-config.json /app/default.project.json

# Production environment variables
ENV ROJO_DEV_MODE=false \
    ROJO_LIVE_RELOAD=false \
    ROJO_LOG_LEVEL=info \
    RUST_LOG=warn

# Create necessary directories
RUN mkdir -p /app/logs /app/builds && \
    chown -R rojo:rojo /app/logs /app/builds

# Security hardening
USER rojo

# Production health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:34872/api/rojo/health || exit 1

# Production entrypoint
ENTRYPOINT ["tini", "--"]
CMD ["rojo", "serve", \
     "--address", "0.0.0.0", \
     "--port", "34872", \
     "--project", "/app/default.project.json"]

# ============================================
# DEPLOYMENT STAGE - For automated deployments
# ============================================
FROM production AS deployment

# Install Python for deployment scripts
USER root
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment for deployment tools
RUN python3 -m venv /opt/deploy-venv && \
    /opt/deploy-venv/bin/pip install --upgrade pip && \
    /opt/deploy-venv/bin/pip install \
        requests==2.31.* \
        httpx==0.25.* \
        pydantic==2.* \
        rich==13.*

# Copy deployment scripts
COPY --chown=rojo:rojo roblox/scripts/deploy.py /app/scripts/deploy.py
COPY --chown=rojo:rojo roblox/scripts/asset_upload.py /app/scripts/asset_upload.py

# Environment for deployment
ENV PATH="/opt/deploy-venv/bin:$PATH" \
    PYTHONPATH=/app \
    DEPLOYMENT_MODE=automated

USER rojo

# Deployment command
CMD ["/opt/deploy-venv/bin/python", "/app/scripts/deploy.py", "--auto"]