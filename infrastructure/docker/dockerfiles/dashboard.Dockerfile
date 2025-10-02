# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI DASHBOARD DOCKERFILE
# ============================================
# Multi-stage build optimized for Docker Engine 25.x
# Security-first approach with Nginx production deployment
# Updated: 2025-09-25
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
    npm ci --only=production --no-audit --no-fund --cache /app/.npm-cache && \
    npm cache clean --force

# Copy source code
COPY --chown=builduser:builduser apps/dashboard/ ./

# Build arguments for environment variables
ARG NODE_ENV=production
ARG VITE_API_BASE_URL=http://backend:8009
ARG VITE_PUSHER_KEY
ARG VITE_PUSHER_CLUSTER=us2
ARG VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
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

# Create comprehensive nginx configuration
RUN cat > /etc/nginx/nginx.conf << 'NGINX_CONF_EOF'
user nginx-app;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Permitted-Cross-Domain-Policies "none" always;
    add_header X-Download-Options "noopen" always;

    # Enhanced CSP for ToolBoxAI Dashboard with all service integrations
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://clerk.toolboxai.app https://*.clerk.accounts.dev https://js.pusher.com https://*.pusher.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; font-src 'self' data: https://fonts.gstatic.com https://fonts.googleapis.com; img-src 'self' data: https: blob:; connect-src 'self' https: wss: ws: https://*.pusher.com wss://*.pusher.com http://localhost:8009 http://localhost:9877 http://localhost:8888 http://localhost:5001 http://localhost:8000; media-src 'self' data: blob:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self';" always;

    server_tokens off;

    include /etc/nginx/conf.d/*.conf;
}
NGINX_CONF_EOF

# Create server configuration
RUN cat > /etc/nginx/conf.d/default.conf << 'NGINX_DEFAULT_CONF_EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Security headers specific to this server
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 '{"status":"healthy","service":"dashboard-frontend","timestamp":"$time_iso8601"}';
        add_header Content-Type application/json;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://backend:8009/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket support for real-time features
    location /ws/ {
        proxy_pass http://backend:8009/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Pusher auth endpoint
    location /pusher/ {
        proxy_pass http://backend:8009/pusher/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # MCP Server proxy
    location /mcp/ {
        proxy_pass http://mcp-server:9877/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Agent Coordinator proxy
    location /agents/ {
        proxy_pass http://agent-coordinator:8888/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Roblox Bridge proxy
    location /roblox/ {
        proxy_pass http://flask-bridge:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Ghost CMS proxy
    location /ghost/ {
        proxy_pass http://ghost-backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # React Router - handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;

        # Cache HTML files for shorter periods
        location ~* \.html$ {
            expires 1h;
            add_header Cache-Control "public, must-revalidate";
        }
    }

    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
NGINX_DEFAULT_CONF_EOF

# Create entrypoint script for production
RUN cat > /docker-entrypoint.sh << 'DOCKER_ENTRYPOINT_EOF' && \
    chmod +x /docker-entrypoint.sh && \
    chown nginx-app:nginx-app /docker-entrypoint.sh
#!/bin/bash
set -e

echo "🚀 Starting ToolBoxAI Dashboard Frontend"
echo "📊 Configuration:"
echo "  - User: $(id)"
echo "  - Working directory: $(pwd)"
echo "  - Nginx version: $(nginx -v 2>&1)"
echo "  - Files in web root: $(ls -la /usr/share/nginx/html | wc -l) files"

# Test nginx configuration
echo "🔍 Testing Nginx configuration..."
nginx -t

# Start nginx with proper signal handling
echo "✅ Starting Nginx server..."
exec nginx -g "daemon off;"
DOCKER_ENTRYPOINT_EOF

# Set proper ownership for all files
RUN chown -R nginx-app:nginx-app /etc/nginx/conf.d/ \
                                 /usr/share/nginx/html \
                                 /var/log/nginx \
                                 /var/cache/nginx \
                                 /run/nginx

# Add metadata labels
LABEL org.opencontainers.image.title="ToolBoxAI Dashboard Frontend" \
      org.opencontainers.image.description="React dashboard with Nginx for ToolBoxAI" \
      org.opencontainers.image.vendor="ToolBoxAI Solutions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-09-25" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      org.opencontainers.image.documentation="https://docs.toolboxai.solutions" \
      org.opencontainers.image.licenses="MIT"

# Switch to non-root user
USER nginx-app

# Expose port 80
EXPOSE 80

# Enhanced health check with multiple fallbacks
HEALTHCHECK --interval=30s --timeout=15s --start-period=40s --retries=5 \
    CMD curl -f http://localhost/health || \
        curl -f http://localhost/ || \
        wget --quiet --tries=1 --spider http://localhost/ || \
        exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the application
CMD ["/docker-entrypoint.sh"]