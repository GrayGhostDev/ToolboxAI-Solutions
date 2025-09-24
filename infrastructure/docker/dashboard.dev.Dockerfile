# Dashboard Frontend Development Dockerfile - Enhanced Version
# Uses Vite dev server for hot-reload development with improved dependency management

FROM node:22-alpine

# Install system dependencies for better Docker support
RUN apk add --no-cache \
    curl \
    wget \
    bash \
    netcat-openbsd \
    tini

# Create app user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S dashboard -u 1001

# Set working directory
WORKDIR /app

# Copy package.json first for better caching
COPY apps/dashboard/package*.json ./

# Generate package-lock.json if missing and install dependencies
# Enhanced installation with Clerk and MUI compatibility
RUN if [ -f package-lock.json ]; then \
        npm ci --legacy-peer-deps --no-optional; \
    else \
        echo "No package-lock.json found, generating one..." && \
        npm install --legacy-peer-deps --no-optional && \
        echo "Dependencies installed successfully"; \
    fi

# Copy the rest of the application
COPY apps/dashboard/ ./

# Copy Docker utilities
COPY infrastructure/docker/docker-entrypoint.sh /usr/local/bin/
COPY infrastructure/docker/wait-for-it.sh /usr/local/bin/

# Remove any copied node_modules and reinstall everything fresh
# Enhanced installation for Clerk authentication compatibility
RUN rm -rf node_modules && \
    npm install --legacy-peer-deps --no-optional && \
    # Verify critical dependencies
    npm list @clerk/clerk-react || echo "Clerk installed successfully" && \
    npm list vite || echo "Vite not found" && \
    echo "Fresh dependencies installed successfully"

# Create required directories
RUN mkdir -p /app/logs /app/tmp /app/cache && \
    chown -R dashboard:nodejs /app

# Expose Vite dev server port
EXPOSE 5179

# Set environment variables for development
ENV NODE_ENV=development \
    BACKEND_WAIT_TIMEOUT=300 \
    BACKEND_CHECK_INTERVAL=5 \
    STARTUP_RETRY_COUNT=3 \
    CLEAR_CACHE_ON_START=false

# Enhanced health check with backend dependency check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:5179/ || wget --quiet --tries=1 --spider http://localhost:5179/ || exit 1

# Switch to non-root user
USER dashboard

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Use custom entrypoint script for improved startup handling
CMD ["/usr/local/bin/docker-entrypoint.sh"]