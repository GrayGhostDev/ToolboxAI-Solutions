FROM pgbouncer/pgbouncer:1.22.0-alpine

# Install additional tools for monitoring and debugging
RUN apk add --no-cache \
    postgresql-client \
    curl \
    bash \
    openssl

# Create necessary directories
RUN mkdir -p /var/log/pgbouncer /var/run/pgbouncer /etc/pgbouncer

# Copy configuration files
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt
COPY entrypoint.sh /entrypoint.sh

# Set proper permissions
RUN chmod 600 /etc/pgbouncer/userlist.txt && \
    chmod 644 /etc/pgbouncer/pgbouncer.ini && \
    chmod +x /entrypoint.sh && \
    chown -R pgbouncer:pgbouncer /var/log/pgbouncer /var/run/pgbouncer /etc/pgbouncer

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD pg_isready -h localhost -p 6432 -U pgbouncer_stats -d pgbouncer || exit 1

# Expose PgBouncer port
EXPOSE 6432

# Switch to pgbouncer user
USER pgbouncer

# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]