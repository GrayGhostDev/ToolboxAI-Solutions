# Flask Bridge Dockerfile for Roblox Integration
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (install requirements.txt for all dependencies)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir flask-socketio==5.3.6 && \
    pip install --no-cache-dir gunicorn

# Copy application code with correct structure
COPY --chown=appuser:appuser apps/backend apps/backend
COPY --chown=appuser:appuser core core
COPY --chown=appuser:appuser database database
COPY --chown=appuser:appuser toolboxai_settings toolboxai_settings

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app/logs /app/tmp

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/status || exit 1

# Start Flask with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "apps.backend.flask_bridge:app"]