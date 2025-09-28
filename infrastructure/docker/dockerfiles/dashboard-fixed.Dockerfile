# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI DASHBOARD DOCKERFILE - 2025 FIXED
# ============================================
# Multi-stage build optimized for Docker Engine 25.x
# Security-first approach with Nginx production deployment
# Updated: 2025-09-27 - Fixed build issues
# ============================================

# ============================================
# BUILDER STAGE - Node.js build environment
# ============================================
FROM node:20-alpine AS builder

# Install security updates and build dependencies
RUN apk update && apk upgrade && \
    apk add --no-cache \
        python3 \
        make \
        g++ \
        curl \
        git \
        bash \
    && rm -rf /var/cache/apk/*

# Create non-root user for build process
RUN addgroup -g 1002 -S builduser && \
    adduser -S -u 1002 -G builduser -h /app -s /sbin/nologin builduser

# Set working directory
WORKDIR /app

# Set Node.js environment variables for build
ENV NODE_ENV=production \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false \
    GENERATE_SOURCEMAP=false \
    DISABLE_ESLINT_PLUGIN=true

# Copy package files for dependency installation
COPY --chown=builduser:builduser apps/dashboard/package*.json ./

# Install dependencies with cache mount for faster builds
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    --mount=type=cache,target=/app/.npm-cache,sharing=locked \
    npm install --production --no-audit --no-fund --cache /app/.npm-cache && \
    npm cache clean --force

# Copy source code
COPY --chown=builduser:builduser apps/dashboard/ ./

# Build arguments for environment variables
ARG NODE_ENV=production
ARG VITE_API_BASE_URL=http://backend:8009
ARG VITE_PUSHER_KEY
ARG VITE_PUSHER_CLUSTER=us2
ARG VITE_PUSHER_AUTH_ENDPOINT=/api/pusher/auth
ARG VITE_PUSHER_SSL=true
ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_ENABLE_WEBSOCKET=false
ARG VITE_ENABLE_PUSHER=true
ARG VITE_ENABLE_GAMIFICATION=true
ARG VITE_ENABLE_ANALYTICS=true
ARG VITE_ENABLE_MCP=true
ARG VITE_ENABLE_AGENTS=true
ARG VITE_ENABLE_ROBLOX=true
ARG VITE_ENABLE_GHOST=true

# Set build environment variables
ENV NODE_ENV=${NODE_ENV} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_PUSHER_KEY=${VITE_PUSHER_KEY} \
    VITE_PUSHER_CLUSTER=${VITE_PUSHER_CLUSTER} \
    VITE_PUSHER_AUTH_ENDPOINT=${VITE_PUSHER_AUTH_ENDPOINT} \
    VITE_PUSHER_SSL=${VITE_PUSHER_SSL} \
    VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY} \
    VITE_ENABLE_WEBSOCKET=${VITE_ENABLE_WEBSOCKET} \
    VITE_ENABLE_PUSHER=${VITE_ENABLE_PUSHER} \
    VITE_ENABLE_GAMIFICATION=${VITE_ENABLE_GAMIFICATION} \
    VITE_ENABLE_ANALYTICS=${VITE_ENABLE_ANALYTICS} \
    VITE_ENABLE_MCP=${VITE_ENABLE_MCP} \
    VITE_ENABLE_AGENTS=${VITE_ENABLE_AGENTS} \
    VITE_ENABLE_ROBLOX=${VITE_ENABLE_ROBLOX} \
    VITE_ENABLE_GHOST=${VITE_ENABLE_GHOST}

# Switch to non-root user for build
USER builduser

# Build the application with comprehensive error handling
RUN set -e && \
    echo "🔨 Building ToolBoxAI Dashboard..." && \
    npm run build && \
    echo "✅ Build completed successfully" && \
    ls -la dist/ && \
    # Verify essential files exist
    test -f dist/index.html || (echo "❌ index.html not found in dist/" && exit 1) && \
    find dist -name "*.js" | head -1 | grep -q ".js" || (echo "❌ No JS files found in dist/" && exit 1) && \
    echo "✅ Build verification passed"

# ============================================
# PRODUCTION STAGE - Nginx with enhanced security
# ============================================
FROM nginx:1.25-alpine AS production

# Install security updates and runtime dependencies
RUN apk update && apk upgrade && \
    apk add --no-cache \
        curl \
        wget \
        bash \
        tini \
        ca-certificates \
    && rm -rf /var/cache/apk/*

# Create nginx user with specific UID/GID for security
RUN addgroup -g 1002 -S nginx-app && \
    adduser -S -u 1002 -G nginx-app -h /var/cache/nginx -s /sbin/nologin nginx-app

# Create required directories with proper permissions
RUN mkdir -p /usr/share/nginx/html \
             /var/log/nginx \
             /var/cache/nginx \
             /run/nginx \
             /etc/nginx/templates \
             /usr/share/nginx/html/health && \
    chown -R nginx-app:nginx-app /usr/share/nginx/html \
                                /var/log/nginx \
                                /var/cache/nginx \
                                /run/nginx

# Copy built application from builder stage
COPY --from=builder --chown=nginx-app:nginx-app /app/dist /usr/share/nginx/html

# Create nginx configuration using multiple RUN commands to avoid heredoc issues
RUN echo 'user nginx-app;' > /etc/nginx/nginx.conf
RUN echo 'worker_processes auto;' >> /etc/nginx/nginx.conf
RUN echo 'error_log /var/log/nginx/error.log notice;' >> /etc/nginx/nginx.conf
RUN echo 'pid /run/nginx.pid;' >> /etc/nginx/nginx.conf
RUN echo '' >> /etc/nginx/nginx.conf
RUN echo 'events {' >> /etc/nginx/nginx.conf
RUN echo '    worker_connections 1024;' >> /etc/nginx/nginx.conf
RUN echo '    use epoll;' >> /etc/nginx/nginx.conf
RUN echo '    multi_accept on;' >> /etc/nginx/nginx.conf
RUN echo '}' >> /etc/nginx/nginx.conf
RUN echo '' >> /etc/nginx/nginx.conf
RUN echo 'http {' >> /etc/nginx/nginx.conf
RUN echo '    include /etc/nginx/mime.types;' >> /etc/nginx/nginx.conf
RUN echo '    default_type application/octet-stream;' >> /etc/nginx/nginx.conf
RUN echo '    sendfile on;' >> /etc/nginx/nginx.conf
RUN echo '    tcp_nopush on;' >> /etc/nginx/nginx.conf
RUN echo '    tcp_nodelay on;' >> /etc/nginx/nginx.conf
RUN echo '    keepalive_timeout 65;' >> /etc/nginx/nginx.conf
RUN echo '    types_hash_max_size 2048;' >> /etc/nginx/nginx.conf
RUN echo '    client_max_body_size 10M;' >> /etc/nginx/nginx.conf
RUN echo '    gzip on;' >> /etc/nginx/nginx.conf
RUN echo '    gzip_vary on;' >> /etc/nginx/nginx.conf
RUN echo '    gzip_min_length 1024;' >> /etc/nginx/nginx.conf
RUN echo '    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;' >> /etc/nginx/nginx.conf
RUN echo '    add_header X-Frame-Options "SAMEORIGIN" always;' >> /etc/nginx/nginx.conf
RUN echo '    add_header X-Content-Type-Options "nosniff" always;' >> /etc/nginx/nginx.conf
RUN echo '    add_header X-XSS-Protection "1; mode=block" always;' >> /etc/nginx/nginx.conf
RUN echo '    add_header Referrer-Policy "strict-origin-when-cross-origin" always;' >> /etc/nginx/nginx.conf
RUN echo '    add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\'' https://clerk.toolboxai.app https://*.clerk.accounts.dev https://js.pusher.com https://*.pusher.com; style-src '\''self'\'' '\''unsafe-inline'\'' https://fonts.googleapis.com; font-src '\''self'\'' data: https://fonts.gstatic.com; img-src '\''self'\'' data: https: blob:; connect-src '\''self'\'' https: wss: ws: https://*.pusher.com wss://*.pusher.com; media-src '\''self'\'' data:; object-src '\''none'\''; base-uri '\''self'\''; form-action '\''self'\'';" always;' >> /etc/nginx/nginx.conf
RUN echo '    server_tokens off;' >> /etc/nginx/nginx.conf
RUN echo '    include /etc/nginx/conf.d/*.conf;' >> /etc/nginx/nginx.conf
RUN echo '}' >> /etc/nginx/nginx.conf

# Create server configuration
RUN echo 'server {' > /etc/nginx/conf.d/default.conf
RUN echo '    listen 80;' >> /etc/nginx/conf.d/default.conf
RUN echo '    listen [::]:80;' >> /etc/nginx/conf.d/default.conf
RUN echo '    server_name _;' >> /etc/nginx/conf.d/default.conf
RUN echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf
RUN echo '    index index.html;' >> /etc/nginx/conf.d/default.conf
RUN echo '    location /health {' >> /etc/nginx/conf.d/default.conf
RUN echo '        access_log off;' >> /etc/nginx/conf.d/default.conf
RUN echo '        return 200 '\''{"status":"healthy","service":"dashboard-frontend","timestamp":"$time_iso8601"}'\'';' >> /etc/nginx/conf.d/default.conf
RUN echo '        add_header Content-Type application/json;' >> /etc/nginx/conf.d/default.conf
RUN echo '    }' >> /etc/nginx/conf.d/default.conf
RUN echo '    location /api/ {' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_pass http://backend:8009/;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header Host $host;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/conf.d/default.conf
RUN echo '    }' >> /etc/nginx/conf.d/default.conf
RUN echo '    location /pusher/ {' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_pass http://backend:8009/pusher/;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header Host $host;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/conf.d/default.conf
RUN echo '        proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/conf.d/default.conf
RUN echo '    }' >> /etc/nginx/conf.d/default.conf
RUN echo '    location / {' >> /etc/nginx/conf.d/default.conf
RUN echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/conf.d/default.conf
RUN echo '    }' >> /etc/nginx/conf.d/default.conf
RUN echo '}' >> /etc/nginx/conf.d/default.conf

# Create simple entrypoint script
RUN echo '#!/bin/bash' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo 'echo "🚀 Starting ToolBoxAI Dashboard Frontend"' >> /docker-entrypoint.sh && \
    echo 'nginx -t' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    chown nginx-app:nginx-app /docker-entrypoint.sh

# Set proper ownership for all files
RUN chown -R nginx-app:nginx-app /etc/nginx/conf.d/ \
                                 /usr/share/nginx/html \
                                 /var/log/nginx \
                                 /var/cache/nginx \
                                 /run/nginx

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Dashboard Frontend" \
      org.opencontainers.image.description="React dashboard with Pusher + Mantine v8" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.created="2025-09-27" \
      toolboxai.pusher.enabled="true" \
      toolboxai.mantine.version="8.3.1"

# Switch to non-root user
USER nginx-app

# Expose port 80
EXPOSE 80

# Enhanced health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=40s --retries=5 \
    CMD curl -f http://localhost/health || \
        curl -f http://localhost/ || \
        exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the application
CMD ["/docker-entrypoint.sh"]
