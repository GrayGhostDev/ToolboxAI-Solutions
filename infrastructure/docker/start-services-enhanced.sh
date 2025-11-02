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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILES=(
    "-f" "$PROJECT_DIR/infrastructure/docker/compose/docker-compose.yml"
    "-f" "$PROJECT_DIR/infrastructure/docker/compose/docker-compose.dev.yml"
)
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

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    log_error "Docker Compose plugin or docker-compose binary not found"
    exit 1
fi

COMPOSE_DISPLAY="${COMPOSE_CMD[*]}"

compose() {
    "${COMPOSE_CMD[@]}" "${COMPOSE_FILES[@]}" "$@"
}

DEFAULT_PROFILES="week2,production,migration"
if [[ -z "${COMPOSE_PROFILES:-}" ]]; then
    export COMPOSE_PROFILES="$DEFAULT_PROFILES"
    log_info "Using default COMPOSE_PROFILES: $COMPOSE_PROFILES"
fi

AVAILABLE_SERVICES=""
SERVICE_FILTER_DISABLED=false
if ! AVAILABLE_SERVICES="$(compose config --services 2>/dev/null)"; then
    SERVICE_FILTER_DISABLED=true
    log_warn "Unable to enumerate compose services. All start commands will be attempted."
fi

service_available() {
    local service="$1"
    if [[ "$SERVICE_FILTER_DISABLED" == true ]]; then
        return 0
    fi
    printf '%s\n' "$AVAILABLE_SERVICES" | grep -qx "$service"
}

# Function to check if docker and docker-compose are available
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    local compose_missing=false
    for compose_file in "${COMPOSE_FILES[@]}"; do
        case "$compose_file" in
            -f)
                continue
                ;;
            *)
                if [ ! -f "$compose_file" ]; then
                    log_error "Docker Compose file not found: $compose_file"
                    compose_missing=true
                fi
                ;;
        esac
    done

    if [ "$compose_missing" = true ]; then
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
        local status
        status=$(compose ps "$service" --format "{{.Health}}" 2>/dev/null || echo "unknown")

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
        local status
        status=$(compose ps "$service" --format "{{.State}}" 2>/dev/null || echo "unknown")

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
    compose logs --tail="$lines" "$service" || true
}

# Function to start a service with error handling
start_service() {
    local service=$1
    local build=${2:-false}
    local wait_for_health=${3:-true}

    if ! service_available "$service"; then
        log_warn "Skipping $service (not defined in current compose files)"
        return 0
    fi

    if [ "$build" = "true" ]; then
        log_info "🔨 Building $service..."
        if ! compose build "$service"; then
            log_error "Failed to build $service"
            show_service_logs "$service"
            return 1
        fi
    fi

    log_info "🚀 Starting $service..."
    if ! compose up -d "$service"; then
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
    compose down --remove-orphans 2>/dev/null || true
    log_success "✅ Cleanup completed"
}

# Function to show final status
show_status() {
    log_info "📊 Final Service Status:"
    echo
    compose ps --format "table {{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}"
    echo
}

# Function to show service URLs
show_service_urls() {
    log_info "🔗 Service URLs:"
    cat << EOF
  🗄️  PostgreSQL:        localhost:5434
  🔄  Redis:             localhost:6381
  🚀  Backend API:       http://localhost:8009
  📘  API Docs:          http://localhost:8009/docs
  🤖  MCP Server:        http://localhost:9877
  🎯  Agent Coordinator: http://localhost:8888
  ⚙️  Celery Flower:     http://localhost:5555
  🖥️  Dashboard (Vite):  http://localhost:5179
  🗂️  Adminer:           http://localhost:8080
  🧭  Redis Commander:   http://localhost:8081
  ✉️  Mailhog:           http://localhost:8025
  📈  Prometheus:        http://localhost:9090
  🎮  Roblox Sync:       http://localhost:34872

📝 Useful commands:
  View logs: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} logs -f <service>
  Stop all: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} down
  Restart:  $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} restart <service>
  Status:   $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} ps
EOF
}

# Main execution function
main() {
    log_info "============================================"
    log_info "🚀 ToolBoxAI Docker Services - Enhanced Startup"
    log_info "============================================"

    # Run prerequisites before starting
    check_prerequisites

    # Ensure we operate from project root for any relative commands
    cd "$PROJECT_DIR" || {
        log_error "Unable to change directory to project root: $PROJECT_DIR"
        exit 1
    }

    # Cleanup any existing containers
    cleanup_containers

    # Start services in dependency order
    log_info "📦 Phase 1: Starting infrastructure services..."

    # Phase 1: Infrastructure (databases, cache)
    start_service "postgres" false true || exit 1
    start_service "redis" false true || exit 1

    log_info "📦 Phase 2: Starting core backend services..."

    # Phase 2: Core backend services
    start_service "backend" true true || exit 1
    start_service "mcp-server" true true || exit 1

    log_info "📦 Phase 3: Starting orchestration services..."

    # Phase 3: Orchestration and async workers
    start_service "agent-coordinator" true true || exit 1
    start_service "celery-worker" true true || exit 1
    start_service "celery-beat" true true || exit 1
    start_service "celery-flower" true true || exit 1
    start_service "flower" false false || exit 1

    log_info "📦 Phase 4: Starting extended platform services..."

    # Phase 4: Extended services and observability
    start_service "roblox-sync" true true || exit 1
    start_service "redis-cloud-connector" false false || exit 1
    start_service "backup-coordinator" false true || exit 1
    start_service "migration-runner" false true || exit 1
    start_service "prometheus" false false || exit 1

    log_info "📦 Phase 5: Starting frontend and tooling..."

    # Phase 5: Frontend and developer tooling
    start_service "dashboard" true true || exit 1
    start_service "adminer" false false || exit 1
    start_service "redis-commander" false false || exit 1
    start_service "mailhog" false false || exit 1

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
