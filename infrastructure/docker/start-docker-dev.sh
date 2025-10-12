#!/bin/bash
# ToolBoxAI Docker Development Environment Startup Script
# This script validates configuration and starts all services in the correct order

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILES=(
    "-f" "$PROJECT_ROOT/infrastructure/docker/compose/docker-compose.yml"
    "-f" "$PROJECT_ROOT/infrastructure/docker/compose/docker-compose.dev.yml"
)
ENV_FILE="$PROJECT_ROOT/.env"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [SETUP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SETUP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [SETUP]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [SETUP]${NC} $1"
}

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    log_error "Docker Compose plugin or binary not found. Install Docker Desktop 4.29+."
    exit 1
fi

COMPOSE_DISPLAY="${COMPOSE_CMD[*]}"

compose() {
    "${COMPOSE_CMD[@]}" "${COMPOSE_FILES[@]}" "$@"
}

# Function to check if Docker is running
check_docker() {
    log "Checking Docker status..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker Desktop."
        return 1
    fi
    
    log_success "Docker is running"
    return 0
}

# Function to validate environment file
validate_env_file() {
    log "Validating environment file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        return 1
    fi
    
    # Check for required environment variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "JWT_SECRET_KEY"
        "PUSHER_KEY"
        "PUSHER_SECRET"
        "PUSHER_APP_ID"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || [ "$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2)" = "" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing or empty required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        return 1
    fi
    
    log_success "Environment file validated"
    return 0
}

# Function to check for port conflicts
check_port_conflicts() {
    log "Checking for port conflicts..."
    
    local ports=(8009 5179 5434 6381 8888 9877 5555 8080 8081 8025)
    local conflicts=()
    
    for port in "${ports[@]}"; do
        if lsof -i ":$port" &> /dev/null; then
            conflicts+=("$port")
        fi
    done
    
    if [ ${#conflicts[@]} -gt 0 ]; then
        log_warn "The following ports are already in use:"
        for port in "${conflicts[@]}"; do
            log_warn "  - Port $port: $(lsof -i ":$port" | tail -n +2 | awk '{print $1}' | head -1)"
        done
        log_warn "Docker Compose will attempt to use these ports. You may need to stop conflicting services."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    else
        log_success "No port conflicts found"
    fi
    
    return 0
}

# Function to validate Dockerfiles
validate_dockerfiles() {
    log "Validating Dockerfiles..."
    
    local dockerfiles=(
        "infrastructure/docker/dockerfiles/backend.Dockerfile"
        "infrastructure/docker/dockerfiles/dashboard-2025.Dockerfile"
        "infrastructure/docker/dockerfiles/mcp.Dockerfile"
        "infrastructure/docker/dockerfiles/agents.Dockerfile"
        "infrastructure/docker/dockerfiles/celery-worker.Dockerfile"
        "infrastructure/docker/dockerfiles/celery-beat.Dockerfile"
        "infrastructure/docker/dockerfiles/celery-flower.Dockerfile"
        "infrastructure/docker/dockerfiles/roblox-sync.Dockerfile"
    )
    
    local missing_files=()
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [ ! -f "$dockerfile" ]; then
            missing_files+=("$dockerfile")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "Missing Dockerfiles:"
        for file in "${missing_files[@]}"; do
            log_error "  - $file"
        done
        return 1
    fi
    
    log_success "All Dockerfiles found"
    return 0
}

# Function to validate docker-compose file
validate_compose_file() {
    log "Validating docker-compose file..."
    
    if ! compose config --quiet; then
        log_error "Docker Compose file validation failed"
        return 1
    fi
    
    log_success "Docker Compose file is valid"
    return 0
}

# Function to clean up previous containers and volumes
cleanup_previous_run() {
    log "Cleaning up previous Docker resources..."
    
    # Stop and remove containers
    compose down --remove-orphans --volumes 2>/dev/null || true
    
    # Remove dangling images (optional)
    docker image prune -f > /dev/null 2>&1 || true
    
    log_success "Cleanup completed"
}

# Function to pull base images
pull_base_images() {
    log "Pulling base Docker images..."
    
    local base_images=(
        "postgres:16-alpine"
        "redis:7-alpine"
        "python:3.12-slim"
        "node:22-alpine"
        "hashicorp/vault:latest"
    )
    
    for image in "${base_images[@]}"; do
        log "Pulling $image..."
        docker pull "$image" || log_warn "Failed to pull $image (will build from cache)"
    done
    
    log_success "Base images updated"
}

# Function to build services
build_services() {
    log "Building Docker services..."
    
    if ! compose build --parallel; then
        log_error "Failed to build services"
        return 1
    fi
    
    log_success "All services built successfully"
    return 0
}

# Function to start services in phases
start_services() {
    log "Starting services in phases..."

    # Phase 1: Database and cache services
    log "Phase 1: Starting database and cache services..."
    compose up -d postgres redis

    # Wait for databases to be ready
    log "Waiting for PostgreSQL to be ready..."
    local postgres_ready=false
    for i in {1..30}; do
        if compose exec -T postgres pg_isready -U "${POSTGRES_USER:-toolboxai}" -d "${POSTGRES_DB:-toolboxai}" 2>/dev/null; then
            postgres_ready=true
            break
        fi
        log "PostgreSQL not ready yet, waiting... ($i/30)"
        sleep 5
    done
    
    if [ "$postgres_ready" = false ]; then
        log_error "PostgreSQL failed to become ready"
        return 1
    fi

    log "Waiting for Redis to be ready..."
    local redis_ready=false
    for i in {1..15}; do
        if compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
            redis_ready=true
            break
        fi
        log "Redis not ready yet, waiting... ($i/15)"
        sleep 2
    done
    
    if [ "$redis_ready" = false ]; then
        log_error "Redis failed to become ready"
        return 1
    fi
    
    log_success "Database and cache services are ready"

    # Phase 2: Backend services
    log "Phase 2: Starting backend services..."
    compose up -d backend

    # Wait for backend to be ready
    log "Waiting for FastAPI backend to be ready..."
    sleep 30

    # Phase 3: MCP and agent services
    log "Phase 3: Starting MCP and agent services..."
    compose up -d mcp-server
    sleep 15
    compose up -d agent-coordinator
    sleep 10
    compose up -d celery-worker celery-beat

    # Phase 4: Observability and tooling
    log "Phase 4: Starting observability services..."
    compose up -d flower

    sleep 10

    # Phase 5: Frontend
    log "Phase 5: Starting frontend..."
    compose up -d dashboard adminer redis-commander mailhog

    log_success "All services started"
}

# Function to verify services are running
verify_services() {
    log "Verifying service health..."
    
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts..."
        
        # Check each service
        local services_status=""
        
        # Backend health
        if curl -f -s -m 5 http://localhost:8009/health > /dev/null; then
            services_status+="✓ Backend (8009) "
        else
            services_status+="✗ Backend (8009) "
        fi
        
        # Dashboard health
        if curl -f -s -m 5 http://localhost:5179/ > /dev/null; then
            services_status+="✓ Dashboard (5179) "
        else
            services_status+="✗ Dashboard (5179) "
        fi
        
        # MCP Server health
        if curl -f -s -m 5 http://localhost:9877/health > /dev/null; then
            services_status+="✓ MCP (9877) "
        else
            services_status+="✗ MCP (9877) "
        fi
        
        # Agent Coordinator health
        if curl -f -s -m 5 http://localhost:8888/health > /dev/null; then
            services_status+="✓ Agents (8888) "
        else
            services_status+="✗ Agents (8888) "
        fi
        
        # Flower health (optional)
        if curl -f -s -m 5 http://localhost:5555/ > /dev/null; then
            services_status+="✓ Flower (5555) "
        else
            services_status+="✗ Flower (5555) "
        fi

        log "$services_status"
        
        # Check if all services are healthy
        if [[ ! "$services_status" == *"✗"* ]]; then
            log_success "All services are healthy!"
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            log "Waiting 15 seconds before next check..."
            sleep 15
        fi
        
        attempt=$((attempt + 1))
    done
    
    log_warn "Some services may not be fully ready yet. Check $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} logs for details."
    return 0
}

# Function to show service URLs
show_service_urls() {
    log_success "============================================"
    log_success "ToolBoxAI Development Environment Ready!"
    log_success "============================================"
    echo
    log_success "Service URLs:"
    log_success "• Dashboard Frontend: http://localhost:5179"
    log_success "• FastAPI Backend:   http://localhost:8009"
    log_success "• API Documentation: http://localhost:8009/docs"
    log_success "• MCP Server:        http://localhost:9877"
    log_success "• Agent Coordinator: http://localhost:8888"
    log_success "• Celery Flower:     http://localhost:5555"
    log_success "• Adminer:           http://localhost:8080"
    log_success "• Redis Commander:   http://localhost:8081"
    log_success "• Mailhog:           http://localhost:8025"
    echo
    log_success "Database Connections:"
    log_success "• PostgreSQL: localhost:5434"
    log_success "• Redis: localhost:6381"
    echo
    log_success "To view logs: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} logs -f <service>"
    log_success "To stop all services: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} down"
    echo
}

# Function to show logs menu
show_logs_menu() {
    echo
    log "Would you like to view logs for any service?"
    echo "1) All services"
    echo "2) Dashboard frontend"
    echo "3) FastAPI backend"
    echo "4) Agent coordinator"
    echo "5) Skip logs"
    
    read -p "Choose an option (1-5): " -n 1 -r
    echo
    
    case $REPLY in
        1) compose logs -f ;;
        2) compose logs -f dashboard ;;
        3) compose logs -f backend ;;
        4) compose logs -f agent-coordinator ;;
        5) ;;
        *) log_warn "Invalid option" ;;
    esac
}

# Main execution function
main() {
    # Change to project root
    cd "$PROJECT_ROOT" || {
        log_error "Cannot change to project root: $PROJECT_ROOT"
        exit 1
    }
    
    log "============================================"
    log "ToolBoxAI Docker Development Setup"
    log "============================================"
    log "Project: $PROJECT_ROOT"
    log "Compose command: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]}"
    echo
    
    # Run all validation steps
    local validation_steps=(
        "check_docker"
        "validate_env_file"
        "validate_dockerfiles"
        "validate_compose_file"
        "check_port_conflicts"
    )
    
    for step in "${validation_steps[@]}"; do
        if ! $step; then
            log_error "Validation failed at step: $step"
            exit 1
        fi
    done
    
    log_success "All validation checks passed!"
    echo
    
    # Ask user if they want to continue
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        log "Assuming yes and continuing..."
    fi
    
    # Execution steps
    local execution_steps=(
        "cleanup_previous_run"
        "pull_base_images"
        "build_services"
        "start_services"
        "verify_services"
    )
    
    for step in "${execution_steps[@]}"; do
        if ! $step; then
            log_error "Execution failed at step: $step"
            exit 1
        fi
    done
    
    # Show final status
    show_service_urls
    show_logs_menu
}

# Handle script interruption
trap 'log_warn "Setup interrupted by user"; exit 130' INT TERM

# Execute main function
main "$@"
