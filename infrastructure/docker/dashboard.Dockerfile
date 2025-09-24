# Dashboard Frontend Dockerfile - Multi-stage build for production
# Enhanced with better security, build optimization, and health checks

# Build stage
FROM node:22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache python3 make g++ curl

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY apps/dashboard/package*.json ./

# Clean existing artifacts to prevent conflicts
RUN rm -rf node_modules package-lock.json .vite dist

# Install dependencies with enhanced configuration
RUN npm install --legacy-peer-deps --no-optional && \
    npm cache clean --force

# Copy source code
COPY apps/dashboard/ ./

# Copy wait script for build-time dependency checking
COPY infrastructure/docker/wait-for-it.sh /usr/local/bin/

# Build arguments for environment variables
ARG NODE_ENV=production
ARG VITE_API_BASE_URL
ARG VITE_PUSHER_KEY
ARG VITE_PUSHER_CLUSTER
ARG VITE_PUSHER_AUTH_ENDPOINT
ARG VITE_PUSHER_SSL=true
ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_ENABLE_WEBSOCKET=true
ARG VITE_ENABLE_GAMIFICATION=true
ARG VITE_ENABLE_ANALYTICS=true

# Set build environment
ENV NODE_ENV=${NODE_ENV} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_PUSHER_KEY=${VITE_PUSHER_KEY} \
    VITE_PUSHER_CLUSTER=${VITE_PUSHER_CLUSTER} \
    VITE_PUSHER_AUTH_ENDPOINT=${VITE_PUSHER_AUTH_ENDPOINT} \
    VITE_PUSHER_SSL=${VITE_PUSHER_SSL} \
    VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY} \
    VITE_ENABLE_WEBSOCKET=${VITE_ENABLE_WEBSOCKET} \
    VITE_ENABLE_GAMIFICATION=${VITE_ENABLE_GAMIFICATION} \
    VITE_ENABLE_ANALYTICS=${VITE_ENABLE_ANALYTICS} \
    GENERATE_SOURCEMAP=false

# Build the application with error handling
RUN set -e && \
    echo "Building application..." && \
    npm run build && \
    echo "Build completed successfully" && \
    ls -la dist/ && \
    # Verify essential files exist
    test -f dist/index.html || (echo "❌ index.html not found in dist/" && exit 1) && \
    echo "✅ Build verification passed"

# Production stage - Nginx with enhanced security
FROM nginx:alpine

# Install required packages for health checks and security
RUN apk add --no-cache \
    curl \
    wget \
    bash \
    tini \
    && rm -rf /var/cache/apk/*

# Create nginx user with specific UID/GID for security
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -u 1001 -G nginx-user nginx-user

# Create required directories
RUN mkdir -p /usr/share/nginx/html /var/log/nginx /var/cache/nginx /run/nginx

# Copy nginx configuration files
COPY infrastructure/docker/nginx.conf /etc/nginx/nginx.conf
COPY infrastructure/docker/default.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder --chown=nginx-user:nginx-user /app/dist /usr/share/nginx/html

# Create comprehensive security headers configuration
RUN cat > /etc/nginx/conf.d/security.conf << 'EOF'
# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Permitted-Cross-Domain-Policies "none" always;
add_header X-Download-Options "noopen" always;

# Content Security Policy - Enhanced for ToolBoxAI Dashboard
add_header Content-Security-Policy "default-src 'self'; \
    script-src 'self' 'unsafe-inline' 'unsafe-eval' https://clerk.toolboxai.app https://*.clerk.accounts.dev https://js.pusher.com; \
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; \
    font-src 'self' data: https://fonts.gstatic.com; \
    img-src 'self' data: https: blob:; \
    connect-src 'self' https: wss: ws:; \
    media-src 'self' data:; \
    object-src 'none'; \
    base-uri 'self'; \
    form-action 'self';" always;

# Additional security measures
server_tokens off;
client_max_body_size 10M;
EOF

# Create health check endpoint
RUN mkdir -p /usr/share/nginx/html/health && \
    echo '{"status":"healthy","service":"dashboard-frontend","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' > /usr/share/nginx/html/health/index.json

# Set proper ownership
RUN chown -R nginx-user:nginx-user /usr/share/nginx/html \
    /var/log/nginx \
    /var/cache/nginx \
    /run/nginx \
    /etc/nginx/conf.d/

# Create entrypoint script for production
RUN cat > /docker-entrypoint-prod.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting ToolBoxAI Dashboard Frontend (Production)"
echo "📊 Build info:"
echo "  - Timestamp: $(date)"
echo "  - User: $(id)"
echo "  - Working directory: $(pwd)"
echo "  - Nginx config test:"

# Test nginx configuration
nginx -t

# Start nginx with proper signal handling
echo "✅ Starting Nginx..."
exec nginx -g "daemon off;"
EOF

RUN chmod +x /docker-entrypoint-prod.sh

# Copy wait script
COPY --from=builder /usr/local/bin/wait-for-it.sh /usr/local/bin/

# Expose port 80
EXPOSE 80

# Enhanced health check with multiple fallbacks
HEALTHCHECK --interval=30s --timeout=15s --start-period=40s --retries=5 \
    CMD curl -f http://localhost/health/ || \
        curl -f http://localhost/ || \
        wget --quiet --tries=1 --spider http://localhost/ || \
        exit 1

# Security: Switch to non-root user
USER nginx-user

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the application
CMD ["/docker-entrypoint-prod.sh"]

# Metadata labels
LABEL maintainer="ToolBoxAI Solutions" \
      version="1.0.0" \
      description="ToolBoxAI Dashboard Frontend - Production" \
      service="dashboard-frontend"