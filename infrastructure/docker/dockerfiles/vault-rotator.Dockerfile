FROM python:3.12-slim

# Security: Run as non-root user
RUN groupadd -r rotator && useradd -r -g rotator rotator

# Install dependencies
WORKDIR /app
COPY requirements-rotator.txt .
RUN pip install --no-cache-dir -r requirements-rotator.txt

# Copy application
COPY infrastructure/scripts/vault_rotator.py .

# Set ownership
RUN chown -R rotator:rotator /app

# Switch to non-root user
USER rotator

# Run the rotator
CMD ["python", "vault_rotator.py"]

