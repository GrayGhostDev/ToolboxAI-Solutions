# syntax=docker/dockerfile:1.6
# ============================================
# TOOLBOXAI BACKEND - SIMPLIFIED BUILD
# ============================================
# Simplified version that works with current structure
# Updated: 2025-09-25

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        netcat-traditional && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r toolboxai && \
    useradd -r -g toolboxai -d /app -s /sbin/nologin toolboxai

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY apps/backend apps/backend
COPY core core
COPY database database
COPY toolboxai_settings toolboxai_settings

# Create necessary directories
RUN mkdir -p /app/logs /app/temp && \
    chown -R toolboxai:toolboxai /app

# Switch to non-root user
USER toolboxai

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1

# Expose port
EXPOSE 8009

# Run the application
CMD ["python", "-m", "uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8009"]
