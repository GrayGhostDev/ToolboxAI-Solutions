# syntax=docker/dockerfile:1.7
# ============================================
# TOOLBOXAI DASHBOARD DOCKERFILE - 2025 OFFICIAL STANDARDS
# ============================================
# Following official Docker + Node.js + Vite 2025 best practices
# Updated: September 27, 2025
# ============================================

# ============================================
# BUILDER STAGE - Node.js 22 LTS (Official 2025)
# ============================================
FROM node:22-alpine AS builder

# Set Node.js environment for build (NOT production to include devDependencies)
ENV NODE_ENV=development \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false \
    GENERATE_SOURCEMAP=false

# Install build dependencies (Alpine 3.20+ official packages)
RUN apk update && apk upgrade && \
    apk add --no-cache \
        python3 \
        make \
        g++ \
        git \
        curl \
        bash \
    && rm -rf /var/cache/apk/*

# Create non-root user (Docker security best practice 2025)
RUN addgroup -g 1001 -S appuser && \
    adduser -S -u 1001 -G appuser -h /app -s /sbin/nologin appuser

# Set working directory
WORKDIR /app

# Copy package files first (Docker layer caching optimization)
COPY --chown=appuser:appuser apps/dashboard/package*.json ./

# Install ALL dependencies (dev dependencies needed for build)
# Using --legacy-peer-deps for React 19 compatibility
RUN --mount=type=cache,target=/home/appuser/.npm,uid=1001,gid=1001 \
    npm install --no-audit --no-fund --legacy-peer-deps && \
    npm cache clean --force

# Copy source code
COPY --chown=appuser:appuser apps/dashboard/ ./

# Build arguments for environment variables
ARG VITE_API_BASE_URL=http://backend:8009
ARG VITE_PUSHER_KEY=dummy-key-for-build
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
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
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

# Switch to non-root user for build (security best practice)
USER appuser

# Build the application (using npm script for proper Vite build)
RUN set -e && \
    echo "🔨 Building ToolBoxAI Dashboard..." && \
    npm run build && \
    echo "✅ Build completed successfully" && \
    ls -la dist/ && \
    # Verify essential files exist
    test -f dist/index.html || (echo "❌ index.html not found" && exit 1) && \
    find dist -name "*.js" | head -1 | grep -q ".js" || (echo "❌ No JS files found" && exit 1) && \
    echo "✅ Build verification passed"

# ============================================
# PRODUCTION STAGE - Nginx 1.26 (Latest stable 2025)
# ============================================
FROM nginx:1.26-alpine AS production

# Install runtime dependencies (minimal for security)
RUN apk update && apk upgrade && \
    apk add --no-cache \
        curl \
        bash \
        tini \
        ca-certificates \
    && rm -rf /var/cache/apk/*

# Create nginx user with consistent UID/GID
RUN addgroup -g 1001 -S nginxuser && \
    adduser -S -u 1001 -G nginxuser -h /var/cache/nginx -s /sbin/nologin nginxuser

# Create required directories
RUN mkdir -p /usr/share/nginx/html \
             /var/log/nginx \
             /var/cache/nginx \
             /run/nginx && \
    chown -R nginxuser:nginxuser /usr/share/nginx/html \
                                 /var/log/nginx \
                                 /var/cache/nginx \
                                 /run/nginx

# Copy built application from builder stage
COPY --from=builder --chown=nginxuser:nginxuser /app/dist /usr/share/nginx/html

# Create nginx configuration inline (heredoc approach for 2025)
COPY <<EOF /etc/nginx/nginx.conf
user nginxuser;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers (2025 standards)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.pusher.com https://js.pusher.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: https: blob:; connect-src 'self' https: wss: ws: https://*.pusher.com wss://*.pusher.com; media-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self';" always;
    
    server_tokens off;
    include /etc/nginx/conf.d/*.conf;
}
EOF

# Create server configuration
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    listen [::]:80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    
    # Health check
    location /health {
        access_log off;
        return 200 '{"status":"healthy","service":"dashboard","timestamp":"\$time_iso8601"}';
        add_header Content-Type application/json;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://backend:8009/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Pusher auth
    location /pusher/ {
        proxy_pass http://backend:8009/pusher/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # MCP Server proxy
    location /mcp/ {
        proxy_pass http://mcp-server:9877/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Agent Coordinator proxy
    location /agents/ {
        proxy_pass http://agent-coordinator:8888/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }
    
    # React Router fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

# Create simple entrypoint
COPY <<EOF /docker-entrypoint.sh
#!/bin/bash
set -e
echo "🚀 Starting ToolBoxAI Dashboard"
nginx -t
exec nginx -g "daemon off;"
EOF

RUN chmod +x /docker-entrypoint.sh && \
    chown nginxuser:nginxuser /docker-entrypoint.sh

# Set ownership
RUN chown -R nginxuser:nginxuser /etc/nginx/ \
                                 /usr/share/nginx/html \
                                 /var/log/nginx \
                                 /var/cache/nginx \
                                 /run/nginx

# Metadata (OCI standard)
LABEL org.opencontainers.image.title="ToolBoxAI Dashboard" \
      org.opencontainers.image.description="React dashboard with Pusher + Mantine v8" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.created="2025-09-27" \
      org.opencontainers.image.source="https://github.com/ToolBoxAI-Solutions/toolboxai" \
      toolboxai.features="pusher,mantine-v8,mcp,agents,roblox,ghost"

# Security: non-root user
USER nginxuser

# Expose port
EXPOSE 80

# Health check (Docker official format)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Signal handling
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/docker-entrypoint.sh"]
