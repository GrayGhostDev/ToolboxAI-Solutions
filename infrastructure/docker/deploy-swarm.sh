#!/usr/bin/env bash

# ============================================
# ToolboxAI Docker Swarm Deployment Script
# ============================================
# This script handles proper deployment to Docker Swarm
# Usage: ./deploy-swarm.sh [build|deploy|update|remove|status]
# ============================================

set -euo pipefail

# Configuration
STACK_NAME="toolboxai"
COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/compose" && pwd)"
BASE_COMPOSE="${COMPOSE_DIR}/docker-compose.yml"
SWARM_COMPOSE="${COMPOSE_DIR}/docker-compose.swarm.yml"
PROJECT_ROOT="$(cd "${COMPOSE_DIR}/../../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker Swarm is initialized
check_swarm() {
    if ! docker info | grep -q "Swarm: active"; then
        log_error "Docker Swarm is not active"
        echo ""
        echo "Initialize Swarm with:"
        echo "  docker swarm init"
        exit 1
    fi
    log_success "Docker Swarm is active"
}

# Check if required images are built
check_images() {
    log_info "Checking for required Docker images..."

    local images=(
        "toolboxai/backend"
        "toolboxai/dashboard"
        "toolboxai/mcp"
        "toolboxai/agents"
        "toolboxai/celery-worker"
        "toolboxai/celery-beat"
        "toolboxai/celery-flower"
        "toolboxai/roblox-sync"
    )

    local missing=()
    for image in "${images[@]}"; do
        if ! docker images --format "{{.Repository}}" | grep -q "^${image}$"; then
            missing+=("${image}")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_warning "Missing images: ${missing[*]}"
        return 1
    fi

    log_success "All required images are available"
    return 0
}

# Build images using docker-compose
build_images() {
    log_info "Building Docker images..."

    cd "${PROJECT_ROOT}"

    # Use docker-compose to build (not stack deploy)
    docker-compose -f "${BASE_COMPOSE}" build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --parallel

    log_success "Images built successfully"
}

# Create Docker secrets if they don't exist
create_secrets() {
    log_info "Checking Docker secrets..."

    local secrets=(
        "db_password"
        "redis_password"
        "database_url"
        "redis_url"
        "jwt_secret"
        "openai_api_key"
        "anthropic_api_key"
        "roblox_api_key"
        "roblox_client_secret"
        "langcache_api_key"
        "backup_encryption_key"
    )

    local missing=()
    for secret in "${secrets[@]}"; do
        if ! docker secret ls --format "{{.Name}}" | grep -q "^${secret}$"; then
            missing+=("${secret}")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing Docker secrets: ${missing[*]}"
        echo ""
        echo "Create secrets with:"
        echo "  echo 'your-secret-value' | docker secret create <secret-name> -"
        echo ""
        echo "Example:"
        echo "  echo 'mypassword123' | docker secret create db_password -"
        return 1
    fi

    log_success "All required secrets exist"
    return 0
}

# Deploy stack to Swarm
deploy_stack() {
    log_info "Deploying stack to Docker Swarm..."

    # Deploy with both base and swarm override
    docker stack deploy \
        -c "${BASE_COMPOSE}" \
        -c "${SWARM_COMPOSE}" \
        --with-registry-auth \
        --prune \
        "${STACK_NAME}"

    log_success "Stack deployed: ${STACK_NAME}"
    echo ""
    log_info "View services with: docker stack services ${STACK_NAME}"
    log_info "View logs with: docker service logs ${STACK_NAME}_<service-name>"
}

# Update existing stack
update_stack() {
    log_info "Updating stack..."
    deploy_stack
}

# Remove stack from Swarm
remove_stack() {
    log_info "Removing stack from Docker Swarm..."

    if docker stack ls --format "{{.Name}}" | grep -q "^${STACK_NAME}$"; then
        docker stack rm "${STACK_NAME}"
        log_success "Stack removed: ${STACK_NAME}"

        log_info "Waiting for resources to be cleaned up..."
        sleep 10
    else
        log_warning "Stack ${STACK_NAME} not found"
    fi
}

# Show stack status
show_status() {
    if ! docker stack ls --format "{{.Name}}" | grep -q "^${STACK_NAME}$"; then
        log_warning "Stack ${STACK_NAME} is not deployed"
        return 1
    fi

    echo ""
    log_info "Stack Services:"
    docker stack services "${STACK_NAME}"

    echo ""
    log_info "Stack Tasks:"
    docker stack ps "${STACK_NAME}" --no-trunc

    echo ""
    log_info "Networks:"
    docker network ls --filter "name=${STACK_NAME}"

    echo ""
    log_info "Volumes:"
    docker volume ls --filter "name=${STACK_NAME}"
}

# Main deployment flow
full_deploy() {
    log_info "Starting full deployment process..."
    echo ""

    # 1. Check Swarm
    check_swarm
    echo ""

    # 2. Check/Build images
    if ! check_images; then
        log_info "Building missing images..."
        build_images
        echo ""
    fi

    # 3. Check secrets
    if ! create_secrets; then
        exit 1
    fi
    echo ""

    # 4. Deploy
    deploy_stack
    echo ""

    # 5. Show status
    log_info "Waiting for services to start..."
    sleep 5
    show_status
}

# Command handler
case "${1:-help}" in
    build)
        check_swarm
        build_images
        ;;
    deploy)
        full_deploy
        ;;
    update)
        check_swarm
        check_images || build_images
        update_stack
        ;;
    remove)
        check_swarm
        remove_stack
        ;;
    status)
        check_swarm
        show_status
        ;;
    help|*)
        echo "ToolboxAI Docker Swarm Deployment"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  build   - Build all Docker images"
        echo "  deploy  - Full deployment (build + secrets check + deploy)"
        echo "  update  - Update existing stack"
        echo "  remove  - Remove stack from Swarm"
        echo "  status  - Show stack status"
        echo "  help    - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 deploy          # Full deployment"
        echo "  $0 update          # Update running stack"
        echo "  $0 status          # Check status"
        echo "  $0 remove          # Remove stack"
        exit 0
        ;;
esac
