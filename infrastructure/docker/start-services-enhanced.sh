#!/bin/bash
# Enhanced ToolBoxAI Docker Services Startup Script
# Includes improved dependency management, health checks, and error handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
PROJECT_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
DOCKER_DIR="$PROJECT_DIR/infrastructure/docker"
MAX_WAIT_TIME=300
CHECK_INTERVAL=5

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

# Function to check if docker and docker-compose are available
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        exit 1
    fi

    if [ ! -f "$DOCKER_DIR/$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $DOCKER_DIR/$COMPOSE_FILE"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Function to check if service is healthy
check_service_health() {
    local service=$1
    local max_attempts=$((MAX_WAIT_TIME / CHECK_INTERVAL))
    local attempt=1

    log_info "⏳ Waiting for $service to be healthy (timeout: ${MAX_WAIT_TIME}s)..."

    while [ $attempt -le $max_attempts ]; do
        local status=$(docker compose -f "$COMPOSE_FILE" ps "$service" --format "{{.Health}}" 2>/dev/null || echo "unknown")

        case "$status" in
            "healthy")
                log_success "✅ $service is healthy (attempt $attempt/$max_attempts)"
                return 0
                ;;
            "unhealthy")
                log_warn "❌ $service is unhealthy (attempt $attempt/$max_attempts)"
                ;;
            "starting")
                log_info "🔄 $service is starting (attempt $attempt/$max_attempts)"
                ;;
            *)
                log_warn "❓ $service status unknown: $status (attempt $attempt/$max_attempts)"
                ;;
        esac

        sleep "$CHECK_INTERVAL"
        attempt=$((attempt + 1))
    done

    log_error "❌ $service failed to become healthy within ${MAX_WAIT_TIME}s"
    return 1
}

# Function to wait for service to be running (not necessarily healthy)
wait_for_service_running() {
    local service=$1
    local max_attempts=$((60 / CHECK_INTERVAL))
    local attempt=1

    log_info "⏳ Waiting for $service to be running..."

    while [ $attempt -le $max_attempts ]; do
        local status=$(docker compose -f "$COMPOSE_FILE" ps "$service" --format "{{.State}}" 2>/dev/null || echo "unknown")

        if [ "$status" = "running" ]; then
            log_success "✅ $service is running"
            return 0
        fi

        log_info "🔄 $service status: $status (attempt $attempt/$max_attempts)"
        sleep "$CHECK_INTERVAL"
        attempt=$((attempt + 1))
    done

    log_error "❌ $service failed to start within 60s"
    return 1
}

# Function to show service logs for debugging
show_service_logs() {
    local service=$1
    local lines=${2:-20}

    log_info "📋 Last $lines lines of logs for $service:"
    docker compose -f "$COMPOSE_FILE" logs --tail="$lines" "$service" || true
}

# Function to start a service with error handling
start_service() {
    local service=$1
    local build=${2:-false}
    local wait_for_health=${3:-true}

    if [ "$build" = "true" ]; then
        log_info "🔨 Building $service..."
        if ! docker compose -f "$COMPOSE_FILE" build "$service" 2>&1 | grep -v "variable is not set" || true; then
            log_error "Failed to build $service"
            show_service_logs "$service"
            return 1
        fi
    fi

    log_info "🚀 Starting $service..."
    if ! docker compose -f "$COMPOSE_FILE" up -d "$service" 2>&1 | grep -v "variable is not set" || true; then
        log_error "Failed to start $service"
        show_service_logs "$service"
        return 1
    fi

    # Wait for service to be running first
    if ! wait_for_service_running "$service"; then
        log_error "Service $service failed to start properly"
        show_service_logs "$service"
        return 1
    fi

    # Check health if the service has health checks
    if [ "$wait_for_health" = "true" ]; then
        if check_service_health "$service"; then
            log_success "✅ $service started successfully and is healthy"
        else
            log_warn "⚠️ $service started but is not healthy"
            show_service_logs "$service"
            # Don't fail here as some services might not have health checks
        fi
    else
        log_success "✅ $service started successfully"
    fi

    return 0
}

# Function to cleanup existing containers
cleanup_containers() {
    log_info "🧹 Cleaning up existing containers..."
    docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    log_success "✅ Cleanup completed"
}

# Function to show final status
show_status() {
    log_info "📊 Final Service Status:"
    echo
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}"
    echo
}

# Function to show service URLs
show_service_urls() {
    log_info "🔗 Service URLs:"
    cat << EOF
  🗄️  PostgreSQL: localhost:5434
  🔄  Redis: localhost:6381
  🚀  FastAPI Backend: http://localhost:8009
  🤖  MCP Server: http://localhost:9877
  🎯  Agent Coordinator: http://localhost:8888
  🌐  Flask Bridge: http://localhost:5001
  🖥️  Dashboard Frontend: http://localhost:5179
  👻  Ghost CMS: http://localhost:8000

📝 Useful commands:
  View logs: docker compose -f $COMPOSE_FILE logs -f [service-name]
  Stop all: docker compose -f $COMPOSE_FILE down
  Restart service: docker compose -f $COMPOSE_FILE restart [service-name]
  Check status: docker compose -f $COMPOSE_FILE ps
EOF
}

# Main execution function
main() {
    log_info "============================================"
    log_info "🚀 ToolBoxAI Docker Services - Enhanced Startup"
    log_info "============================================"

    # Change to docker directory
    cd "$DOCKER_DIR"

    # Check prerequisites
    check_prerequisites

    # Cleanup any existing containers
    cleanup_containers

    # Start services in dependency order
    log_info "📦 Phase 1: Starting infrastructure services..."

    # Phase 1: Infrastructure (databases, cache)
    start_service "postgres" false true || exit 1
    start_service "redis" false true || exit 1

    log_info "📦 Phase 2: Starting core backend services..."

    # Phase 2: Core backend services
    start_service "fastapi-main" true true || exit 1
    start_service "mcp-server" true true || exit 1

    log_info "📦 Phase 3: Starting orchestration services..."

    # Phase 3: Orchestration and agents
    start_service "agent-coordinator" true true || exit 1
    start_service "educational-agents" true false || exit 1  # May not have health check

    log_info "📦 Phase 4: Starting integration services..."

    # Phase 4: Integration services
    start_service "flask-bridge" true true || exit 1

    log_info "📦 Phase 5: Starting frontend and CMS..."

    # Phase 5: Frontend and CMS
    start_service "dashboard-frontend" true true || exit 1
    start_service "ghost-backend" false true || exit 1

    # Final status
    echo
    log_success "🎉 All services started successfully!"
    echo

    show_status
    echo
    show_service_urls

    log_success "✅ ToolBoxAI Docker environment is ready!"
}

# Error handling
trap 'log_error "Script interrupted"; exit 1' INT TERM

# Execute main function if script is run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi