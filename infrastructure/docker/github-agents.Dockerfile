# GitHub Agents Dockerfile
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

# Install Python dependencies with GitHub-specific packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        PyGithub \
        githubpy \
        gitpython \
        cryptography

# Production stage
FROM python:3.12-slim as production

# Install system dependencies for runtime including git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    netcat-openbsd \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r github && useradd -r -g github -s /bin/bash github

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/agents /data/github /app/logs /home/github/.ssh \
    && chown -R github:github /app /data /home/github

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV AGENT_TYPE=github
ENV AGENT_PORT=8080
ENV LOG_LEVEL=info

# Switch to non-root user
USER github

# Expose ports
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run GitHub Agent Pool
CMD ["python", "-m", "core.agents.github_agents.agent_pool"]