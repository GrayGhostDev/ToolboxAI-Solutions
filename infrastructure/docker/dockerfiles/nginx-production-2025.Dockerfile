# syntax=docker/dockerfile:1.7
# ============================================
# TOOLBOXAI NGINX REVERSE PROXY - PRODUCTION 2025
# ============================================
# Target: <50MB
# Minimal Alpine-based reverse proxy with security
# Updated: 2025-10-02
# ============================================

FROM nginx:1.27-alpine AS production

# Install minimal dependencies
RUN apk add --no-cache \
        curl \
        tini \
        ca-certificates \
        openssl && \
    # Create nginx user
    addgroup -g 101 -S nginx || true && \
    adduser -S -u 101 -G nginx nginx || true

# Create required directories
RUN mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
             /var/log/nginx \
             /run/nginx \
             /etc/nginx/ssl && \
    chown -R nginx:nginx \
        /var/cache/nginx \
        /var/log/nginx \
        /run/nginx \
        /etc/nginx

# Create main nginx configuration
COPY <<EOF /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for" '
                    'rt=\$request_time uct=\$upstream_connect_time '
                    'uht=\$upstream_header_time urt=\$upstream_response_time';

    access_log /var/log/nginx/access.log main buffer=32k flush=5s;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    client_body_buffer_size 128k;
    server_tokens off;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/json application/xml+rss
               application/x-javascript text/x-component text/x-cross-domain-policy;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=60r/m;
    limit_req_zone \$binary_remote_addr zone=general:10m rate=120r/m;
    limit_conn_zone \$binary_remote_addr zone=conn_limit:10m;

    # Proxy settings
    proxy_cache_path /var/cache/nginx/proxy levels=1:2 keys_zone=api_cache:10m
                     max_size=500m inactive=60m use_temp_path=off;

    # Security headers (2025 standards)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Upstream configuration
    upstream backend_api {
        least_conn;
        server backend:8009 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream dashboard_app {
        least_conn;
        server dashboard:80 max_fails=3 fail_timeout=30s;
        keepalive 16;
    }

    upstream mcp_server {
        least_conn;
        server mcp-server:9877 max_fails=3 fail_timeout=30s;
        keepalive 16;
    }

    upstream agent_coordinator {
        least_conn;
        server agent-coordinator:8888 max_fails=3 fail_timeout=30s;
        keepalive 16;
    }

    include /etc/nginx/conf.d/*.conf;
}
EOF

# Create server configuration
COPY <<EOF /etc/nginx/conf.d/toolboxai.conf
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Security
    client_body_timeout 30s;
    client_header_timeout 30s;
    send_timeout 60s;

    # Health check
    location /health {
        access_log off;
        return 200 '{"status":"healthy","service":"nginx-proxy","version":"2025.1"}';
        add_header Content-Type application/json;
    }

    # Rate limiting
    limit_req zone=general burst=20 nodelay;
    limit_conn conn_limit 10;

    # Backend API
    location /api/ {
        limit_req zone=api burst=30 nodelay;

        proxy_pass http://backend_api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Request-ID \$request_id;
        proxy_set_header Connection "";

        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;

        # Caching
        proxy_cache api_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        add_header X-Cache-Status \$upstream_cache_status;
    }

    # MCP Server
    location /mcp/ {
        proxy_pass http://mcp_server/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";

        proxy_connect_timeout 30s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }

    # Agent Coordinator
    location /agents/ {
        proxy_pass http://agent_coordinator/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 30s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Dashboard (root)
    location / {
        proxy_pass http://dashboard_app/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}

# HTTPS server (template - requires SSL certificates)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # SSL configuration (update with actual certificates)
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Same location blocks as HTTP server
    include /etc/nginx/conf.d/locations.conf;
}
EOF

# Create entrypoint
COPY <<EOF /docker-entrypoint.sh
#!/bin/sh
set -e
echo "🔧 Testing nginx configuration..."
nginx -t
echo "🚀 Starting nginx reverse proxy..."
exec nginx -g "daemon off;"
EOF

RUN chmod +x /docker-entrypoint.sh && \
    chown nginx:nginx /docker-entrypoint.sh

# Set ownership
RUN chown -R nginx:nginx /etc/nginx /var/log/nginx /var/cache/nginx /run/nginx

# OCI metadata
LABEL org.opencontainers.image.title="ToolBoxAI Nginx Proxy" \
      org.opencontainers.image.description="High-performance reverse proxy (Alpine)" \
      org.opencontainers.image.version="2025.1" \
      org.opencontainers.image.created="2025-10-02" \
      org.opencontainers.image.base.name="nginx:1.27-alpine"

# Non-root user
USER nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Use tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/docker-entrypoint.sh"]
