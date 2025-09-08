# Multi-stage build for ToolboxAI Solutions
FROM python:3.11-slim as python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# Copy requirements and install Python dependencies
COPY src/roblox-environment/requirements-verified.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app database/ ./database/

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Expose port
EXPOSE 8008

# Default command
CMD ["python", "-m", "uvicorn", "src.roblox-environment.server.main:app", "--host", "0.0.0.0", "--port", "8008"]