# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI DASHBOARD DOCKERFILE - DEVELOPMENT
# ============================================
# Lightweight image for Vite hot reload with minimal tooling
# Updated: 2025-10-12
# ============================================

FROM node:22-alpine AS development

# Install build tooling required by npm install (node-gyp deps)
RUN apk update && apk upgrade && \
    apk add --no-cache \
        python3 \
        make \
        g++ \
        bash \
        git && \
    rm -rf /var/cache/apk/*

WORKDIR /app

ENV NODE_ENV=development \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false \
    CHOKIDAR_USEPOLLING=true

# Copy package manifests and install dependencies once
COPY apps/dashboard/package*.json ./
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    npm install --legacy-peer-deps --no-audit --no-fund && \
    npm cache clean --force

# Copy source (will be overridden by bind mounts in dev)
COPY apps/dashboard/ ./

# Expose Vite dev server port
EXPOSE 5179

# Default command: run Vite dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5179"]

