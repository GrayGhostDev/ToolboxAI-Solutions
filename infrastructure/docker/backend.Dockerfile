# Backend API Dockerfile - Multi-stage build for production
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Clear pip cache and install dependencies with explicit upgrade strategy
RUN pip cache purge && \
    pip install --no-cache-dir --user --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user --force-reinstall -r requirements.txt

# Production stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser apps/backend apps/backend
COPY --chown=appuser:appuser core core
COPY --chown=appuser:appuser database database
COPY --chown=appuser:appuser toolboxai_settings toolboxai_settings

# Set Python path
ENV PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app/logs /app/tmp

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8009 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8009}/health || exit 1

# Start command - Use environment variables or defaults
CMD ["sh", "-c", "uvicorn apps.backend.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8009} --workers ${WORKERS:-4} --loop uvloop --access-log"]