# syntax=docker/dockerfile:1.7
# ============================================
# TOOLBOXAI DASHBOARD - PRODUCTION OPTIMIZED 2025
# ============================================
# Target: <100MB (down from ~200MB)
# Optimized multi-stage build with Alpine
# Updated: 2025-10-02
# ============================================

# ============================================
# BUILDER STAGE - Node.js build
# ============================================
FROM node:22-alpine AS builder

# Build environment
ENV NODE_ENV=production \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false \
    GENERATE_SOURCEMAP=false

# Install build dependencies
RUN apk add --no-cache \
        python3 \
        make \
        g++ \
        git

# Create build user
RUN addgroup -g 1001 -S builder && \
    adduser -S -u 1001 -G builder -h /build builder

WORKDIR /build

# Copy package files
COPY --chown=builder:builder apps/dashboard/package*.json ./

# Install dependencies with cache
RUN --mount=type=cache,target=/home/builder/.npm,uid=1001,gid=1001 \
    npm ci --only=production=false --no-audit --no-fund && \
    npm cache clean --force

# Copy source
COPY --chown=builder:builder apps/dashboard/ ./

# Build arguments
ARG VITE_API_BASE_URL=http://backend:8009
ARG VITE_PUSHER_KEY
ARG VITE_PUSHER_CLUSTER=us2
ARG VITE_PUSHER_SSL=true
ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_ENABLE_MCP=true
ARG VITE_ENABLE_AGENTS=true

# Set build environment
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_PUSHER_KEY=${VITE_PUSHER_KEY} \
    VITE_PUSHER_CLUSTER=${VITE_PUSHER_CLUSTER} \
    VITE_PUSHER_SSL=${VITE_PUSHER_SSL} \
    VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY} \
    VITE_ENABLE_MCP=${VITE_ENABLE_MCP} \
    VITE_ENABLE_AGENTS=${VITE_ENABLE_AGENTS}

# Build application
USER builder
RUN npm run build && \
    # Verify build
    test -f dist/index.html && \
    find dist -name "*.js" | head -1 | grep -q ".js" && \
    # Remove unnecessary files
    find dist -name "*.map" -delete && \
    find dist -name "*.txt" -delete

# ============================================
# PRODUCTION STAGE - Nginx minimal
# ============================================
FROM nginx:1.27-alpine AS production

# Install minimal runtime dependencies
RUN apk add --no-cache \
        curl \
        tini \
        ca-certificates && \
    # Create nginx user
    addgroup -g 1001 -S nginxuser && \
    adduser -S -u 1001 -G nginxuser -h /usr/share/nginx/html nginxuser

# Create required directories
RUN mkdir -p /usr/share/nginx/html \
             /var/log/nginx \
             /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
             /run/nginx && \
    chown -R nginxuser:nginxuser \
        /usr/share/nginx/html \
        /var/log/nginx \
        /var/cache/nginx \
        /run/nginx \
        /etc/nginx

# Copy built application
COPY --from=builder --chown=nginxuser:nginxuser /build/dist /usr/share/nginx/html

# Create optimized nginx configuration
COPY <<EOF /etc/nginx/nginx.conf
user nginxuser;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent"';
    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;
    server_tokens off;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/json application/xml+rss;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

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
        return 200 '{"status":"healthy","service":"dashboard"}';
        add_header Content-Type application/json;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend:8009/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static assets with caching
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
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

# Create entrypoint
COPY <<EOF /docker-entrypoint.sh
#!/bin/sh
set -e
echo "🚀 Starting ToolBoxAI Dashboard"
nginx -t
exec nginx -g "daemon off;"
EOF

RUN chmod +x /docker-entrypoint.sh && \
    chown nginxuser:nginxuser /docker-entrypoint.sh /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# OCI metadata
LABEL org.opencontainers.image.title="ToolBoxAI Dashboard" \
      org.opencontainers.image.description="React dashboard (Alpine-optimized)" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.created="2025-10-02" \
      org.opencontainers.image.base.name="nginx:1.27-alpine"

# Non-root user
USER nginxuser

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Use tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/docker-entrypoint.sh"]
