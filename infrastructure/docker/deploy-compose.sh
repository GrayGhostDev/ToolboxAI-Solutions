#!/usr/bin/env bash

# ============================================
# ToolboxAI Docker Compose Deployment Script
# ============================================
# Recommended for Docker Desktop and single-node deployments
# ============================================

set -euo pipefail

# Configuration
COMPOSE_FILE="infrastructure/docker/compose/docker-compose.yml"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Check prerequisites
check_prereqs() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi

    log_success "Prerequisites OK"
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."

    cd "$PROJECT_ROOT"

    mkdir -p infrastructure/config/certificates
    mkdir -p infrastructure/monitoring
    mkdir -p data/postgres

    log_success "Directories created"
}

# Create minimal config files
create_configs() {
    log_info "Creating configuration files..."

    cd "$PROJECT_ROOT"

    # Create certificates placeholder if missing
    if [ ! -f "infrastructure/config/certificates/README.md" ]; then
        echo "# SSL Certificates for Redis Cloud" > infrastructure/config/certificates/README.md
        log_success "Created certificates directory"
    fi

    # Create monitoring config if missing
    if [ ! -f "infrastructure/monitoring/prometheus.yml" ]; then
        cat > infrastructure/monitoring/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8009']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF
        log_success "Created prometheus.yml"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    cd "$PROJECT_ROOT"

    export DOCKER_BUILDKIT=1

    docker-compose -f "$COMPOSE_FILE" build --parallel

    log_success "Images built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."

    cd "$PROJECT_ROOT"

    docker-compose -f "$COMPOSE_FILE" up -d

    log_success "Services started"
}

# Stop services
stop_services() {
    log_info "Stopping services..."

    cd "$PROJECT_ROOT"

    docker-compose -f "$COMPOSE_FILE" down

    log_success "Services stopped"
}

# Show status
show_status() {
    cd "$PROJECT_ROOT"

    echo ""
    log_info "Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    log_info "To view logs:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f [service-name]"
}

# Full deployment
full_deploy() {
    log_info "Starting full deployment..."
    echo ""

    check_prereqs
    echo ""

    create_directories
    echo ""

    create_configs
    echo ""

    build_images
    echo ""

    start_services
    echo ""

    log_info "Waiting for services to stabilize..."
    sleep 10

    show_status
    echo ""

    log_success "Deployment complete!"
    echo ""
    echo "Access points:"
    echo "  Dashboard:  http://localhost:5180"
    echo "  Backend:    http://localhost:8009"
    echo "  Flower:     http://localhost:5555"
    echo "  Roblox:     http://localhost:34872"
}

# Restart services
restart_services() {
    stop_services
    echo ""
    start_services
    echo ""
    show_status
}

# View logs
view_logs() {
    cd "$PROJECT_ROOT"

    if [ -z "${1:-}" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    fi
}

# Main command handler
case "${1:-help}" in
    deploy)
        full_deploy
        ;;
    build)
        check_prereqs
        create_directories
        create_configs
        build_images
        ;;
    start)
        check_prereqs
        start_services
        show_status
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        view_logs "${2:-}"
        ;;
    clean)
        log_warning "Removing all containers, volumes, and networks..."
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" down -v
        log_success "Cleaned up"
        ;;
    help|*)
        echo "ToolboxAI Docker Compose Deployment"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (build + start)"
        echo "  build    - Build all Docker images"
        echo "  start    - Start services"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  status   - Show service status"
        echo "  logs     - View logs (optional: service name)"
        echo "  clean    - Remove all containers and volumes"
        echo "  help     - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 deploy              # Full deployment"
        echo "  $0 logs backend        # View backend logs"
        echo "  $0 restart             # Restart all services"
        ;;
esac
