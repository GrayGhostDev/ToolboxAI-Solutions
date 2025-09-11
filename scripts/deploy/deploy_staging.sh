#!/bin/bash

# ============================================================================
# ToolboxAI Staging Deployment Script
# ============================================================================
# This script deploys the complete ToolboxAI platform to staging environment
# with proper health checks and validation.
#
# Usage: ./deploy_staging.sh [--skip-tests] [--force] [--rollback]
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
ENVIRONMENT="staging"
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
    print_header "CHECKING PREREQUISITES FOR STAGING"

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
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            print_status "Creating .env file from example template..."
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_warning "Please update $PROJECT_ROOT/.env with your actual staging values"
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

    # Check if Python virtual environment exists
    cd "$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
    
    if [ ! -d "venv_clean" ]; then
        print_status "Creating Python virtual environment..."
        python -m venv venv_clean
        source venv_clean/bin/activate
        pip install -r requirements.txt
    else
        print_status "Activating existing virtual environment..."
        source venv_clean/bin/activate
    fi

    # Run basic Python tests
    print_status "Running Python syntax checks..."
    if python -m py_compile server/main.py; then
        print_success "Python syntax check passed"
    else
        print_error "Python syntax check failed"
        if [ "$FORCE_DEPLOY" = false ]; then
            exit 1
        fi
    fi

    # Check database connection scripts
    print_status "Checking database scripts..."
    if [ -f "../database/connection.py" ]; then
        if python -m py_compile ../database/connection.py; then
            print_success "Database connection script syntax check passed"
        else
            print_error "Database connection script syntax check failed"
            if [ "$FORCE_DEPLOY" = false ]; then
                exit 1
            fi
        fi
    fi

    cd "$PROJECT_ROOT"
}

# Function to create staging backup
create_staging_backup() {
    if [ "$BACKUP_BEFORE_DEPLOY" = false ]; then
        print_warning "Skipping backup creation"
        return 0
    fi

    print_header "CREATING STAGING BACKUP"

    local backup_timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="$BACKUP_DIR/staging_backup_$backup_timestamp"

    mkdir -p "$backup_path"

    # Backup configuration files
    print_status "Backing up configuration files..."
    cp -r "$CONFIG_DIR" "$backup_path/config"
    cp "$PROJECT_ROOT/.env" "$backup_path/.env" 2>/dev/null || true
    print_success "Configuration backup created"

    # Backup existing logs
    print_status "Backing up logs..."
    if [ -d "$LOGS_DIR" ]; then
        cp -r "$LOGS_DIR" "$backup_path/logs"
        print_success "Logs backup created"
    fi

    # Create backup manifest
    cat > "$backup_path/backup_manifest.txt" << EOF
Staging Backup created: $(date)
Environment: $ENVIRONMENT
Backup type: Pre-staging-deployment
Files included:
- Configuration files
- Logs
- Environment variables
EOF

    print_success "Staging backup created at: $backup_path"
}

# Function to setup staging database
setup_staging_database() {
    print_header "SETTING UP STAGING DATABASE"

    # Start PostgreSQL container first
    print_status "Starting PostgreSQL container..."
    cd "$CONFIG_DIR"
    
    # Start only PostgreSQL for database setup
    docker-compose -f docker-compose.prod.yml up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec toolboxai-postgres pg_isready -U toolboxai_user -d toolboxai_prod >/dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting for PostgreSQL..."
        sleep 10
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        print_error "PostgreSQL failed to start within timeout"
        exit 1
    fi

    # Run database setup scripts
    print_status "Running database setup scripts..."
    cd "$PROJECT_ROOT"
    
    if [ -f "scripts/setup_database.sh" ]; then
        chmod +x scripts/setup_database.sh
        ./scripts/setup_database.sh --staging
        print_success "Database setup completed"
    else
        print_warning "Database setup script not found, continuing..."
    fi
}

# Function to build and deploy staging services
deploy_staging_services() {
    print_header "DEPLOYING STAGING SERVICES"

    cd "$CONFIG_DIR"

    # Stop any existing services
    print_status "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

    # Build and start services
    print_status "Building and starting staging services..."
    
    # Set staging environment variables
    export COMPOSE_PROJECT_NAME="toolboxai-staging"
    export DATABASE_NAME="toolboxai_staging"
    
    # Start core services first
    print_status "Starting core infrastructure (PostgreSQL, Redis)..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    
    # Wait for core services
    sleep 30
    
    # Start application services
    print_status "Starting application services..."
    docker-compose -f docker-compose.prod.yml up -d fastapi-main flask-bridge
    
    # Wait for application services
    sleep 30
    
    # Start frontend services
    print_status "Starting frontend services..."
    docker-compose -f docker-compose.prod.yml up -d dashboard-backend dashboard-frontend
    
    # Start remaining services
    print_status "Starting remaining services..."
    docker-compose -f docker-compose.prod.yml up -d nginx prometheus grafana
    
    # Wait for all services to stabilize
    print_status "Waiting for all services to stabilize..."
    sleep 60

    print_success "Staging services deployed successfully"
}

# Function to run staging health checks
run_staging_health_checks() {
    print_header "RUNNING STAGING HEALTH CHECKS"

    local services=(
        "fastapi-main:8008"
        "flask-bridge:5001"
        "dashboard-backend:8001"
        "dashboard-frontend:5176"
        "nginx:80"
    )

    local failed_services=()
    local start_time=$(date +%s)

    for service in "${services[@]}"; do
        local service_name=$(echo "$service" | cut -d: -f1)
        local port=$(echo "$service" | cut -d: -f2)

        print_status "Checking health of $service_name..."

        local max_attempts=20
        local attempt=1
        local healthy=false

        while [ $attempt -le $max_attempts ]; do
            # Check if container is running
            if docker ps --format "table {{.Names}}" | grep -q "toolboxai-$service_name" || \
               docker ps --format "table {{.Names}}" | grep -q "$service_name"; then
                
                # Check if service responds
                if curl -s --connect-timeout 5 "http://localhost:$port/health" >/dev/null 2>&1 || \
                   curl -s --connect-timeout 5 "http://localhost:$port/status" >/dev/null 2>&1 || \
                   curl -s --connect-timeout 5 "http://localhost:$port/" >/dev/null 2>&1; then
                    healthy=true
                    break
                fi
            fi

            print_status "Attempt $attempt/$max_attempts - waiting for $service_name..."
            sleep 15
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
        print_success "All staging services are healthy (took ${duration}s)"
        return 0
    else
        print_error "Health check failed for: ${failed_services[*]}"
        return 1
    fi
}

# Function to run staging validation tests
run_staging_validation() {
    print_header "RUNNING STAGING VALIDATION"

    # Test basic connectivity
    print_status "Testing basic service connectivity..."
    
    local endpoints=(
        "http://localhost:8008/health:FastAPI Main"
        "http://localhost:5001/status:Flask Bridge"
        "http://localhost:8001/api/health:Dashboard Backend"
        "http://localhost:5176:Dashboard Frontend"
    )

    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_info" | cut -d: -f1-2)
        local service_name=$(echo "$endpoint_info" | cut -d: -f3)
        
        if curl -s --connect-timeout 10 "$endpoint" >/dev/null 2>&1; then
            print_success "$service_name endpoint accessible: $endpoint"
        else
            print_warning "$service_name endpoint failed: $endpoint"
        fi
    done

    # Test database connectivity
    print_status "Testing database connectivity..."
    if docker exec toolboxai-postgres psql -U toolboxai_user -d toolboxai_prod -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connectivity test passed"
    else
        print_warning "Database connectivity test failed"
    fi

    # Test Redis connectivity
    print_status "Testing Redis connectivity..."
    if docker exec toolboxai-redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis connectivity test passed"
    else
        print_warning "Redis connectivity test failed"
    fi

    print_success "Staging validation completed"
}

# Function to show staging deployment summary
show_staging_summary() {
    print_header "STAGING DEPLOYMENT SUMMARY"

    echo -e "${GREEN}🎉 ToolboxAI Staging Deployment Complete!${NC}"
    echo ""
    echo -e "${BLUE}📊 Staging Service URLs:${NC}"
    echo "  • Main API: http://localhost:8008"
    echo "  • Dashboard Frontend: http://localhost:5176"
    echo "  • Dashboard Backend: http://localhost:8001"
    echo "  • Flask Bridge: http://localhost:5001"
    echo "  • Nginx: http://localhost:80"
    echo ""
    echo -e "${BLUE}📈 Monitoring:${NC}"
    echo "  • Grafana: http://localhost:3000"
    echo "  • Prometheus: http://localhost:9090"
    echo ""
    echo -e "${BLUE}🗄️ Database & Cache:${NC}"
    echo "  • PostgreSQL: localhost:5432"
    echo "  • Redis: localhost:6379"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • View logs: docker-compose -f config/production/docker-compose.prod.yml logs -f"
    echo "  • Stop services: docker-compose -f config/production/docker-compose.prod.yml down"
    echo "  • Restart services: docker-compose -f config/production/docker-compose.prod.yml restart"
    echo "  • Check status: $SCRIPTS_DIR/check_mcp_status.sh"
    echo ""
    echo -e "${YELLOW}⚠️  Next Steps for Production:${NC}"
    echo "  1. Test all functionality thoroughly in staging"
    echo "  2. Update production environment variables"
    echo "  3. Configure SSL certificates"
    echo "  4. Set up production domain and DNS"
    echo "  5. Configure production monitoring alerts"
    echo ""
    echo -e "${GREEN}✨ Staging deployment completed successfully!${NC}"
}

# Function to rollback staging deployment
rollback_staging() {
    print_header "ROLLING BACK STAGING DEPLOYMENT"

    # Find the most recent backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/staging_backup_* 2>/dev/null | head -n1)

    if [ -z "$latest_backup" ]; then
        print_error "No staging backup found for rollback"
        exit 1
    fi

    print_status "Rolling back staging to: $latest_backup"

    # Stop current services
    print_status "Stopping current staging services..."
    cd "$CONFIG_DIR"
    docker-compose -f docker-compose.prod.yml down

    # Restore configuration
    if [ -d "$latest_backup/config" ]; then
        print_status "Restoring configuration..."
        cp -r "$latest_backup/config"/* "$CONFIG_DIR/"
        print_success "Configuration restored"
    fi

    # Restart services
    print_status "Restarting staging services..."
    docker-compose -f docker-compose.prod.yml up -d

    print_success "Staging rollback completed"
}

# Main execution function
main() {
    print_header "TOOLBOXAI STAGING DEPLOYMENT"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
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
                rollback_staging
                exit 0
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-tests         Skip pre-deployment tests"
                echo "  --force              Force deployment even if tests fail"
                echo "  --no-backup          Skip backup creation"
                echo "  --rollback           Rollback to previous staging deployment"
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

    # Run staging deployment steps
    check_prerequisites
    run_pre_deployment_tests
    create_staging_backup
    setup_staging_database
    deploy_staging_services

    # Run health checks and validation
    if run_staging_health_checks; then
        run_staging_validation
        show_staging_summary
        
        # Create deployment report
        local report_file="$PROJECT_ROOT/staging_deployment_report.md"
        cat > "$report_file" << EOF
# ToolboxAI Staging Deployment Report

**Deployment Date:** $(date)
**Environment:** $ENVIRONMENT
**Status:** SUCCESS

## Services Deployed
- FastAPI Main Server (Port 8008)
- Flask Bridge Server (Port 5001)
- Dashboard Backend (Port 8001)
- Dashboard Frontend (Port 5176)
- PostgreSQL Database (Port 5432)
- Redis Cache (Port 6379)
- Nginx Reverse Proxy (Port 80)
- Prometheus Monitoring (Port 9090)
- Grafana Dashboard (Port 3000)

## Health Check Results
All services passed health checks successfully.

## Next Steps
1. Perform comprehensive testing in staging environment
2. Validate all API endpoints and functionality
3. Test user workflows and data persistence
4. Prepare for production deployment

## Rollback Instructions
To rollback this deployment, run:
\`\`\`bash
./scripts/deploy/deploy_staging.sh --rollback
\`\`\`

## Support
For issues or questions, check the logs:
\`\`\`bash
docker-compose -f config/production/docker-compose.prod.yml logs -f
\`\`\`
EOF
        
        print_success "Deployment report created: $report_file"
    else
        print_error "Staging health checks failed. Consider rolling back."
        print_status "To rollback, run: $0 --rollback"
        exit 1
    fi
}

# Run main function
main "$@"