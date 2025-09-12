#!/bin/bash

# ============================================================================
# ToolboxAI Production Deployment Script
# ============================================================================
# This script deploys the complete ToolboxAI platform to production
# with proper health checks, rollback capabilities, and monitoring.
#
# Usage: ./deploy_production.sh [--environment=prod] [--skip-tests] [--force]
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config/production"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
LOGS_DIR="$PROJECT_ROOT/logs"
BACKUP_DIR="$PROJECT_ROOT/backups"

# Deployment settings
ENVIRONMENT="production"
SKIP_TESTS=false
FORCE_DEPLOY=false
BACKUP_BEFORE_DEPLOY=true
HEALTH_CHECK_TIMEOUT=300  # 5 minutes

# Function to print colored output
print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_header "CHECKING PREREQUISITES"

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        exit 1
    fi

    print_success "Docker is installed and running"

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi

    print_success "Docker Compose is available"

    # Check if required files exist
    local required_files=(
        "$CONFIG_DIR/docker-compose.prod.yml"
        "$CONFIG_DIR/production.env"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file not found: $file"
            exit 1
        fi
    done

    print_success "All required configuration files exist"

    # Check if .env file exists or create from template
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$CONFIG_DIR/production.env" ]; then
            print_status "Creating .env file from production template..."
            cp "$CONFIG_DIR/production.env" "$PROJECT_ROOT/.env"
            print_warning "Please update $PROJECT_ROOT/.env with your actual production values"
        else
            print_error "No .env file found and no template available"
            exit 1
        fi
    fi

    print_success "Environment configuration ready"
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_warning "Skipping pre-deployment tests"
        return 0
    fi

    print_header "RUNNING PRE-DEPLOYMENT TESTS"

    # Run integration tests
    print_status "Running integration tests..."
    if [ -f "$SCRIPTS_DIR/integration/verify_integration_paths.sh" ]; then
        if "$SCRIPTS_DIR/integration/verify_integration_paths.sh" --verbose; then
            print_success "Integration tests passed"
        else
            print_error "Integration tests failed"
            if [ "$FORCE_DEPLOY" = false ]; then
                exit 1
            else
                print_warning "Force deploy enabled, continuing despite test failures"
            fi
        fi
    else
        print_warning "Integration test script not found, skipping"
    fi

    # Run unit tests
    print_status "Running unit tests..."
    cd "$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
    if [ -f "pytest.ini" ] && command -v pytest &> /dev/null; then
        if pytest tests/unit/ -v --tb=short; then
            print_success "Unit tests passed"
        else
            print_error "Unit tests failed"
            if [ "$FORCE_DEPLOY" = false ]; then
                exit 1
            else
                print_warning "Force deploy enabled, continuing despite test failures"
            fi
        fi
    else
        print_warning "Unit tests not available, skipping"
    fi

    cd "$PROJECT_ROOT"
}

# Function to create backup
create_backup() {
    if [ "$BACKUP_BEFORE_DEPLOY" = false ]; then
        print_warning "Skipping backup creation"
        return 0
    fi

    print_header "CREATING BACKUP"

    local backup_timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="$BACKUP_DIR/backup_$backup_timestamp"

    mkdir -p "$backup_path"

    # Backup database
    print_status "Backing up databases..."
    if docker ps | grep -q "toolboxai-postgres"; then
        docker exec toolboxai-postgres pg_dumpall -U toolboxai_user > "$backup_path/database_backup.sql"
        print_success "Database backup created"
    else
        print_warning "PostgreSQL container not running, skipping database backup"
    fi

    # Backup configuration files
    print_status "Backing up configuration files..."
    cp -r "$CONFIG_DIR" "$backup_path/config"
    cp "$PROJECT_ROOT/.env" "$backup_path/.env" 2>/dev/null || true
    print_success "Configuration backup created"

    # Backup logs
    print_status "Backing up logs..."
    if [ -d "$LOGS_DIR" ]; then
        cp -r "$LOGS_DIR" "$backup_path/logs"
        print_success "Logs backup created"
    fi

    # Create backup manifest
    cat > "$backup_path/backup_manifest.txt" << EOF
Backup created: $(date)
Environment: $ENVIRONMENT
Backup type: Pre-deployment
Files included:
- Database dump
- Configuration files
- Logs
EOF

    print_success "Backup created at: $backup_path"
}

# Function to build Docker images
build_docker_images() {
    print_header "BUILDING DOCKER IMAGES"

    cd "$PROJECT_ROOT"

    # Build all services
    local services=("fastapi-main" "dashboard-backend" "dashboard-frontend" "ghost-backend" "flask-bridge")

    for service in "${services[@]}"; do
        print_status "Building $service image..."
        if docker build -f "config/production/Dockerfile.$service" -t "toolboxai-$service:latest" .; then
            print_success "$service image built successfully"
        else
            print_error "Failed to build $service image"
            exit 1
        fi
    done

    print_success "All Docker images built successfully"
}

# Function to deploy services
deploy_services() {
    print_header "DEPLOYING SERVICES"

    cd "$CONFIG_DIR"

    # Stop existing services
    print_status "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans || true

    # Start services
    print_status "Starting services..."
    if docker-compose -f docker-compose.prod.yml up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi

    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30

    print_success "Services deployed successfully"
}

# Function to run health checks
run_health_checks() {
    print_header "RUNNING HEALTH CHECKS"

    local services=(
        "fastapi-main:8008"
        "dashboard-backend:8001"
        "dashboard-frontend:5176"
        "ghost-backend:8000"
        "flask-bridge:5001"
        "nginx:80"
    )

    local failed_services=()
    local start_time=$(date +%s)

    for service in "${services[@]}"; do
        local service_name=$(echo "$service" | cut -d: -f1)
        local port=$(echo "$service" | cut -d: -f2)

        print_status "Checking health of $service_name..."

        local max_attempts=30
        local attempt=1
        local healthy=false

        while [ $attempt -le $max_attempts ]; do
            if curl -s --connect-timeout 5 "http://localhost:$port/health" >/dev/null 2>&1 || \
               curl -s --connect-timeout 5 "http://localhost:$port/status" >/dev/null 2>&1 || \
               curl -s --connect-timeout 5 "http://localhost:$port/" >/dev/null 2>&1; then
                healthy=true
                break
            fi

            print_status "Attempt $attempt/$max_attempts - waiting for $service_name..."
            sleep 10
            ((attempt++))
        done

        if [ "$healthy" = true ]; then
            print_success "$service_name is healthy"
        else
            print_error "$service_name failed health check"
            failed_services+=("$service_name")
        fi
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ ${#failed_services[@]} -eq 0 ]; then
        print_success "All services are healthy (took ${duration}s)"
        return 0
    else
        print_error "Health check failed for: ${failed_services[*]}"
        return 1
    fi
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_warning "Skipping post-deployment tests"
        return 0
    fi

    print_header "RUNNING POST-DEPLOYMENT TESTS"

    # Test API endpoints
    print_status "Testing API endpoints..."
    local endpoints=(
        "http://localhost:8008/health"
        "http://localhost:8001/api/health"
        "http://localhost:5001/status"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -s --connect-timeout 10 "$endpoint" >/dev/null 2>&1; then
            print_success "API endpoint accessible: $endpoint"
        else
            print_error "API endpoint failed: $endpoint"
        fi
    done

    # Test database connectivity
    print_status "Testing database connectivity..."
    if docker exec toolboxai-postgres psql -U toolboxai_user -d educational_platform -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connectivity test passed"
    else
        print_error "Database connectivity test failed"
    fi

    # Test Redis connectivity
    print_status "Testing Redis connectivity..."
    if docker exec toolboxai-redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis connectivity test passed"
    else
        print_error "Redis connectivity test failed"
    fi

    print_success "Post-deployment tests completed"
}

# Function to setup monitoring
setup_monitoring() {
    print_header "SETTING UP MONITORING"

    # Check if monitoring services are running
    if docker ps | grep -q "toolboxai-prometheus" && docker ps | grep -q "toolboxai-grafana"; then
        print_success "Monitoring services are running"

        # Wait for Grafana to be ready
        print_status "Waiting for Grafana to be ready..."
        local max_attempts=30
        local attempt=1

        while [ $attempt -le $max_attempts ]; do
            if curl -s --connect-timeout 5 "http://localhost:3000" >/dev/null 2>&1; then
                print_success "Grafana is ready"
                print_status "Grafana dashboard: http://localhost:3000"
                print_status "Prometheus metrics: http://localhost:9090"
                break
            fi

            print_status "Attempt $attempt/$max_attempts - waiting for Grafana..."
            sleep 10
            ((attempt++))
        done
    else
        print_warning "Monitoring services not running"
    fi
}

# Function to show deployment summary
show_deployment_summary() {
    print_header "DEPLOYMENT SUMMARY"

    echo -e "${GREEN}🎉 ToolboxAI Production Deployment Complete!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service URLs:${NC}"
    echo "  • Main API: http://localhost:8008"
    echo "  • Dashboard: http://localhost:5176"
    echo "  • Ghost Backend: http://localhost:8000"
    echo "  • Flask Bridge: http://localhost:5001"
    echo "  • Nginx: http://localhost:80"
    echo ""
    echo -e "${BLUE}📈 Monitoring:${NC}"
    echo "  • Grafana: http://localhost:3000"
    echo "  • Prometheus: http://localhost:9090"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • View logs: docker-compose -f config/production/docker-compose.prod.yml logs -f"
    echo "  • Stop services: docker-compose -f config/production/docker-compose.prod.yml down"
    echo "  • Restart services: docker-compose -f config/production/docker-compose.prod.yml restart"
    echo "  • Check status: $SCRIPTS_DIR/check_mcp_status.sh"
    echo ""
    echo -e "${YELLOW}⚠️  Next Steps:${NC}"
    echo "  1. Update DNS records to point to your server"
    echo "  2. Configure SSL certificates in config/production/ssl/"
    echo "  3. Set up automated backups"
    echo "  4. Configure monitoring alerts"
    echo "  5. Review and update security settings"
    echo ""
    echo -e "${GREEN}✨ Deployment completed successfully!${NC}"
}

# Function to rollback deployment
rollback_deployment() {
    print_header "ROLLING BACK DEPLOYMENT"

    # Find the most recent backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/backup_* 2>/dev/null | head -n1)

    if [ -z "$latest_backup" ]; then
        print_error "No backup found for rollback"
        exit 1
    fi

    print_status "Rolling back to: $latest_backup"

    # Stop current services
    print_status "Stopping current services..."
    cd "$CONFIG_DIR"
    docker-compose -f docker-compose.prod.yml down

    # Restore database
    if [ -f "$latest_backup/database_backup.sql" ]; then
        print_status "Restoring database..."
        docker-compose -f docker-compose.prod.yml up -d postgres
        sleep 30
        docker exec -i toolboxai-postgres psql -U toolboxai_user < "$latest_backup/database_backup.sql"
        print_success "Database restored"
    fi

    # Restore configuration
    if [ -d "$latest_backup/config" ]; then
        print_status "Restoring configuration..."
        cp -r "$latest_backup/config"/* "$CONFIG_DIR/"
        print_success "Configuration restored"
    fi

    # Restart services
    print_status "Restarting services..."
    docker-compose -f docker-compose.prod.yml up -d

    print_success "Rollback completed"
}

# Main execution function
main() {
    print_header "TOOLBOXAI PRODUCTION DEPLOYMENT"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment=*)
                ENVIRONMENT="${1#*=}"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --no-backup)
                BACKUP_BEFORE_DEPLOY=false
                shift
                ;;
            --rollback)
                rollback_deployment
                exit 0
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --environment=ENV    Set deployment environment (default: production)"
                echo "  --skip-tests         Skip pre and post deployment tests"
                echo "  --force              Force deployment even if tests fail"
                echo "  --no-backup          Skip backup creation"
                echo "  --rollback           Rollback to previous deployment"
                echo "  --help, -h           Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$BACKUP_DIR"

    # Run deployment steps
    check_prerequisites
    run_pre_deployment_tests
    create_backup
    build_docker_images
    deploy_services

    # Wait for services to stabilize
    print_status "Waiting for services to stabilize..."
    sleep 60

    # Run health checks
    if run_health_checks; then
        run_post_deployment_tests
        setup_monitoring
        show_deployment_summary
    else
        print_error "Health checks failed. Consider rolling back."
        print_status "To rollback, run: $0 --rollback"
        exit 1
    fi
}

# Run main function
main "$@"
