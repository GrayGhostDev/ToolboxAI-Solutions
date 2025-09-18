# Database Agents Dockerfile
FROM python:3.12-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies with database-specific packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        boto3 \
        pg_dump \
        psycopg2-binary \
        sqlalchemy[postgresql] \
        alembic

# Production stage
FROM python:3.12-slim as production

# Install system dependencies for runtime including PostgreSQL client
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    postgresql-client \
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r dbagent && useradd -r -g dbagent -s /bin/bash dbagent

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/agents /data/backups /app/logs \
    && chown -R dbagent:dbagent /app /data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV AGENT_TYPE=database
ENV AGENT_PORT=8080
ENV LOG_LEVEL=info

# Switch to non-root user
USER dbagent

# Expose ports
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run Database Agent Pool
CMD ["python", "-m", "core.agents.database.agent_pool"]