# Celery Flower Monitoring Dashboard
# Based on official Celery documentation for Flower deployment
# Reference: https://docs.celeryq.dev/en/stable/userguide/monitoring.html#flower-real-time-celery-web-monitor

FROM python:3.12-slim AS base

# Metadata
LABEL maintainer="ToolBoxAI Team"
LABEL description="Celery Flower monitoring dashboard for ToolBoxAI"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -g 1007 flower && \
    useradd -r -u 1007 -g flower -s /sbin/nologin flower

# Set working directory
WORKDIR /app

# ============================================
# Development Stage
# ============================================
FROM base AS development

# Install Flower and dependencies
RUN pip install --no-cache-dir \
    flower==2.0.1 \
    redis>=4.5.0 \
    celery[redis]>=5.3.0

# Copy entrypoint script
COPY --chown=flower:flower <<EOF /app/entrypoint.sh
#!/bin/sh
set -e

echo "Starting Celery Flower monitoring dashboard..."
echo "Broker URL: \${CELERY_BROKER_URL:-redis://redis:6379/0}"
echo "Port: \${FLOWER_PORT:-5555}"

# Start Flower with configuration
exec celery -A apps.backend.celery_app flower \
    --broker=\${CELERY_BROKER_URL:-redis://redis:6379/0} \
    --port=\${FLOWER_PORT:-5555} \
    --address=0.0.0.0 \
    --persistent=true \
    --db=/data/flower.db \
    --max_tasks=10000 \
    --purge_offline_workers=60 \
    --state_save_interval=5000 \
    \${FLOWER_BASIC_AUTH:+--basic_auth=\$FLOWER_BASIC_AUTH} \
    \${FLOWER_URL_PREFIX:+--url_prefix=\$FLOWER_URL_PREFIX}
EOF

RUN chmod +x /app/entrypoint.sh

# Create data directory for persistent storage
RUN mkdir -p /data && chown -R flower:flower /data

# Switch to non-root user
USER flower

# Expose Flower port
EXPOSE 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${FLOWER_PORT:-5555}/api/workers || exit 1

# Volume for persistent data
VOLUME ["/data"]

# Start Flower
ENTRYPOINT ["/app/entrypoint.sh"]

# ============================================
# Production Stage
# ============================================
FROM base AS production

# Install production dependencies only
RUN pip install --no-cache-dir \
    flower==2.0.1 \
    redis>=4.5.0 \
    celery[redis]>=5.3.0

# Copy application code
COPY --chown=flower:flower . /app

# Copy entrypoint from development stage
COPY --from=development --chown=flower:flower /app/entrypoint.sh /app/entrypoint.sh

# Create data directory
RUN mkdir -p /data && chown -R flower:flower /data

# Security hardening for production
RUN chmod 500 /app/entrypoint.sh && \
    find /app -type d -exec chmod 755 {} \; && \
    find /app -type f -exec chmod 644 {} \;

# Switch to non-root user
USER flower

# Expose Flower port
EXPOSE 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${FLOWER_PORT:-5555}/api/workers || exit 1

# Volume for persistent data
VOLUME ["/data"]

# Start Flower
ENTRYPOINT ["/app/entrypoint.sh"]