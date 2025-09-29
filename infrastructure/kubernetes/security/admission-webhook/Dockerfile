# Security Admission Webhook for Kubernetes
FROM python:3.11-slim-bookworm AS builder

# Security: Run as non-root user
RUN groupadd -r webhook && useradd -r -g webhook -u 1000 webhook

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim-bookworm

# Import user from builder
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy Python packages
COPY --from=builder --chown=webhook:webhook /root/.local /home/webhook/.local

# Copy application
WORKDIR /app
COPY --chown=webhook:webhook main.py .

# Security hardening
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Remove unnecessary tools
    rm -rf /usr/bin/wget /usr/bin/curl && \
    # Make filesystem read-only except for /tmp
    chmod -R 555 /app && \
    chmod 1777 /tmp

# Switch to non-root user
USER webhook

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/webhook/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:443/health', verify=False).raise_for_status()"

# Expose HTTPS port
EXPOSE 443

# Run the webhook server
ENTRYPOINT ["python", "-u", "main.py"]