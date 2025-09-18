# Dashboard Backend Dockerfile
FROM node:22-slim

# Create non-root user - check if UID 1000 exists first
RUN if id -u 1000 >/dev/null 2>&1; then \
        usermod -l appuser $(id -un 1000) || true; \
    else \
        useradd -m -u 1000 -s /bin/bash appuser; \
    fi

# Set working directory
WORKDIR /app

# Install dependencies for node-gyp
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY apps/backend/package*.json ./

# Install dependencies
RUN npm install --production --legacy-peer-deps

# Copy application code
COPY apps/backend/ .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Start the application
CMD ["node", "server.js"]