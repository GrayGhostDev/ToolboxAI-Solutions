#!/bin/bash

# PgBouncer Deployment Script
# Deploys and configures PgBouncer for production use

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/../../.env}"
ENVIRONMENT="${ENVIRONMENT:-production}"
DOCKER_COMPOSE_FILE="docker-compose.pgbouncer.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Creating template .env file..."
        create_env_template
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Create environment template
create_env_template() {
    cat > "$ENV_FILE" <<EOF
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=toolboxai_production
POSTGRES_USER=toolboxai
POSTGRES_PASSWORD=your_secure_password_here

# Service Passwords (optional - defaults to POSTGRES_PASSWORD)
API_DB_PASSWORD=
AGENT_DB_PASSWORD=
WEBSOCKET_DB_PASSWORD=

# PgBouncer Configuration
PGBOUNCER_POOL_MODE=transaction
PGBOUNCER_POOL_SIZE=25
PGBOUNCER_MAX_CLIENT_CONN=2000
PGBOUNCER_MAX_DB_CONNECTIONS=100

# Environment
ENVIRONMENT=production
EOF
    log_info "Template .env file created at $ENV_FILE"
}

# Generate secure passwords
generate_passwords() {
    log_info "Generating secure passwords for userlist.txt..."

    # Source environment variables
    source "$ENV_FILE"

    # Function to generate MD5 hash
    generate_md5() {
        local password="$1"
        local username="$2"
        echo -n "md5$(echo -n "${password}${username}" | md5sum | cut -d' ' -f1)"
    }

    # Generate userlist.txt with actual passwords
    cat > "$SCRIPT_DIR/userlist.txt" <<EOF
# PgBouncer user authentication file
# Generated on $(date)

"${POSTGRES_USER}" "$(generate_md5 "$POSTGRES_PASSWORD" "$POSTGRES_USER")"
"postgres" "$(generate_md5 "$POSTGRES_PASSWORD" "postgres")"
"pgbouncer_admin" "$(generate_md5 "$POSTGRES_PASSWORD" "pgbouncer_admin")"
"pgbouncer_stats" "$(generate_md5 "$POSTGRES_PASSWORD" "pgbouncer_stats")"
"monitoring" "$(generate_md5 "$POSTGRES_PASSWORD" "monitoring")"
EOF

    # Add service accounts if passwords are provided
    if [ -n "$API_DB_PASSWORD" ]; then
        echo "\"api_service\" \"$(generate_md5 "$API_DB_PASSWORD" "api_service")\"" >> "$SCRIPT_DIR/userlist.txt"
    fi

    if [ -n "$AGENT_DB_PASSWORD" ]; then
        echo "\"agent_service\" \"$(generate_md5 "$AGENT_DB_PASSWORD" "agent_service")\"" >> "$SCRIPT_DIR/userlist.txt"
    fi

    if [ -n "$WEBSOCKET_DB_PASSWORD" ]; then
        echo "\"websocket_service\" \"$(generate_md5 "$WEBSOCKET_DB_PASSWORD" "websocket_service")\"" >> "$SCRIPT_DIR/userlist.txt"
    fi

    chmod 600 "$SCRIPT_DIR/userlist.txt"
    log_info "userlist.txt generated with secure passwords"
}

# Build Docker image
build_image() {
    log_info "Building PgBouncer Docker image..."
    cd "$SCRIPT_DIR"
    docker build -t toolboxai-pgbouncer:latest .
    log_info "Docker image built successfully"
}

# Deploy PgBouncer
deploy() {
    log_info "Deploying PgBouncer..."

    cd "$SCRIPT_DIR"

    # Stop existing containers if any
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        log_warn "Stopping existing PgBouncer containers..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
    fi

    # Start PgBouncer
    log_info "Starting PgBouncer..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    # Wait for PgBouncer to be ready
    log_info "Waiting for PgBouncer to be ready..."
    sleep 5

    # Check health
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "healthy"; then
        log_info "PgBouncer is healthy and running"
    else
        log_warn "PgBouncer health check failed. Checking logs..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50 pgbouncer
    fi
}

# Test connection
test_connection() {
    log_info "Testing PgBouncer connection..."

    # Source environment variables
    source "$ENV_FILE"

    # Test connection through PgBouncer
    docker run --rm --network=toolboxai-network postgres:16-alpine \
        psql -h pgbouncer -p 6432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" \
        || log_error "Connection test failed"

    log_info "Connection test completed"
}

# Monitor PgBouncer
monitor() {
    log_info "Monitoring PgBouncer statistics..."

    # Connect to PgBouncer admin console
    docker exec -it toolboxai-pgbouncer psql -h localhost -p 6432 -U pgbouncer_stats -d pgbouncer -c "SHOW STATS;"
    docker exec -it toolboxai-pgbouncer psql -h localhost -p 6432 -U pgbouncer_stats -d pgbouncer -c "SHOW POOLS;"
    docker exec -it toolboxai-pgbouncer psql -h localhost -p 6432 -U pgbouncer_stats -d pgbouncer -c "SHOW DATABASES;"
}

# Show usage
usage() {
    echo "Usage: $0 {deploy|test|monitor|stop|logs|help}"
    echo ""
    echo "Commands:"
    echo "  deploy   - Deploy PgBouncer with Docker Compose"
    echo "  test     - Test PgBouncer connection"
    echo "  monitor  - Show PgBouncer statistics"
    echo "  stop     - Stop PgBouncer containers"
    echo "  logs     - Show PgBouncer logs"
    echo "  help     - Show this help message"
}

# Main execution
main() {
    case "$1" in
        deploy)
            check_prerequisites
            generate_passwords
            build_image
            deploy
            test_connection
            ;;
        test)
            test_connection
            ;;
        monitor)
            monitor
            ;;
        stop)
            log_info "Stopping PgBouncer..."
            cd "$SCRIPT_DIR"
            docker-compose -f "$DOCKER_COMPOSE_FILE" down
            log_info "PgBouncer stopped"
            ;;
        logs)
            cd "$SCRIPT_DIR"
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f pgbouncer
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"