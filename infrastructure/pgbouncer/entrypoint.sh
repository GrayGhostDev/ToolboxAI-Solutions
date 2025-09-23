#!/bin/bash
set -e

# Function to generate MD5 password hash for PgBouncer
generate_md5_hash() {
    local password="$1"
    local username="$2"
    echo -n "md5$(echo -n "${password}${username}" | md5sum | cut -d' ' -f1)"
}

# Update userlist.txt with environment variables if provided
if [ -n "$POSTGRES_PASSWORD" ] && [ -n "$POSTGRES_USER" ]; then
    echo "Updating userlist with environment credentials..."

    # Generate MD5 hashes
    POSTGRES_HASH=$(generate_md5_hash "$POSTGRES_PASSWORD" "$POSTGRES_USER")

    # Create userlist dynamically
    cat > /etc/pgbouncer/userlist.txt <<EOF
"$POSTGRES_USER" "$POSTGRES_HASH"
"postgres" "$POSTGRES_HASH"
"pgbouncer_admin" "$POSTGRES_HASH"
"pgbouncer_stats" "$POSTGRES_HASH"
"monitoring" "$POSTGRES_HASH"
EOF

    # Add service-specific users if provided
    if [ -n "$API_DB_PASSWORD" ]; then
        echo "\"api_service\" \"$(generate_md5_hash "$API_DB_PASSWORD" "api_service")\"" >> /etc/pgbouncer/userlist.txt
    fi

    if [ -n "$AGENT_DB_PASSWORD" ]; then
        echo "\"agent_service\" \"$(generate_md5_hash "$AGENT_DB_PASSWORD" "agent_service")\"" >> /etc/pgbouncer/userlist.txt
    fi

    if [ -n "$WEBSOCKET_DB_PASSWORD" ]; then
        echo "\"websocket_service\" \"$(generate_md5_hash "$WEBSOCKET_DB_PASSWORD" "websocket_service")\"" >> /etc/pgbouncer/userlist.txt
    fi

    chmod 600 /etc/pgbouncer/userlist.txt
fi

# Update pgbouncer.ini with environment variables
if [ -n "$POSTGRES_HOST" ]; then
    echo "Updating pgbouncer.ini with database host: $POSTGRES_HOST"
    sed -i "s/host=postgres/host=$POSTGRES_HOST/g" /etc/pgbouncer/pgbouncer.ini
fi

if [ -n "$POSTGRES_PORT" ]; then
    echo "Updating pgbouncer.ini with database port: $POSTGRES_PORT"
    sed -i "s/port=5432/port=$POSTGRES_PORT/g" /etc/pgbouncer/pgbouncer.ini
fi

if [ -n "$POSTGRES_DB" ]; then
    echo "Updating pgbouncer.ini with database name: $POSTGRES_DB"
    sed -i "s/dbname=toolboxai_production/dbname=$POSTGRES_DB/g" /etc/pgbouncer/pgbouncer.ini
fi

# Configure pool sizes based on environment
if [ -n "$PGBOUNCER_POOL_SIZE" ]; then
    echo "Setting default pool size: $PGBOUNCER_POOL_SIZE"
    sed -i "s/default_pool_size = 25/default_pool_size = $PGBOUNCER_POOL_SIZE/g" /etc/pgbouncer/pgbouncer.ini
fi

if [ -n "$PGBOUNCER_MAX_CLIENT_CONN" ]; then
    echo "Setting max client connections: $PGBOUNCER_MAX_CLIENT_CONN"
    sed -i "s/max_client_conn = 2000/max_client_conn = $PGBOUNCER_MAX_CLIENT_CONN/g" /etc/pgbouncer/pgbouncer.ini
fi

if [ -n "$PGBOUNCER_MAX_DB_CONNECTIONS" ]; then
    echo "Setting max database connections: $PGBOUNCER_MAX_DB_CONNECTIONS"
    sed -i "s/max_db_connections = 100/max_db_connections = $PGBOUNCER_MAX_DB_CONNECTIONS/g" /etc/pgbouncer/pgbouncer.ini
fi

# Set pool mode if specified
if [ -n "$PGBOUNCER_POOL_MODE" ]; then
    echo "Setting pool mode: $PGBOUNCER_POOL_MODE"
    sed -i "s/pool_mode = transaction/pool_mode = $PGBOUNCER_POOL_MODE/g" /etc/pgbouncer/pgbouncer.ini
fi

# Enable verbose logging for development
if [ "$ENVIRONMENT" = "development" ]; then
    echo "Enabling verbose logging for development"
    sed -i "s/verbose = 2/verbose = 3/g" /etc/pgbouncer/pgbouncer.ini
fi

# Wait for PostgreSQL to be ready
if [ -n "$WAIT_FOR_POSTGRES" ] && [ "$WAIT_FOR_POSTGRES" = "true" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
    POSTGRES_PORT="${POSTGRES_PORT:-5432}"

    until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done

    echo "PostgreSQL is ready!"
fi

# Start PgBouncer
echo "Starting PgBouncer..."
exec pgbouncer /etc/pgbouncer/pgbouncer.ini