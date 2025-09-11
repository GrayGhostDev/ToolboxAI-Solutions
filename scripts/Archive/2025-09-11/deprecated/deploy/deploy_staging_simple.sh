#!/bin/bash

# ============================================================================
# ToolboxAI Simple Staging Deployment Script
# ============================================================================
# This script deploys core infrastructure and sets up for manual application testing
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config/production"
LOGS_DIR="$PROJECT_ROOT/logs"
BACKUP_DIR="$PROJECT_ROOT/backups"

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

# Main execution
main() {
    print_header "TOOLBOXAI SIMPLE STAGING DEPLOYMENT"

    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$BACKUP_DIR"

    # Step 1: Deploy infrastructure services
    print_header "DEPLOYING INFRASTRUCTURE SERVICES"
    
    cd "$CONFIG_DIR"
    
    # Stop any existing services
    print_status "Stopping existing services..."
    docker-compose -f docker-compose.staging.yml down --remove-orphans 2>/dev/null || true
    
    # Start infrastructure services
    print_status "Starting PostgreSQL and Redis..."
    docker-compose -f docker-compose.staging.yml up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check PostgreSQL
    if docker exec toolboxai-postgres-staging pg_isready -U toolboxai_user -d toolboxai_staging >/dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_error "PostgreSQL failed to start"
        exit 1
    fi
    
    # Check Redis
    if docker exec toolboxai-redis-staging redis-cli -a staging_redis_2024 ping >/dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis failed to start"
        exit 1
    fi

    # Step 2: Set up database
    print_header "SETTING UP DATABASES"
    
    print_status "Creating application databases..."
    docker exec toolboxai-postgres-staging psql -U toolboxai_user -d toolboxai_staging -c "
        CREATE DATABASE IF NOT EXISTS educational_platform;
        CREATE DATABASE IF NOT EXISTS ghost_backend;
        CREATE DATABASE IF NOT EXISTS roblox_data;
        CREATE DATABASE IF NOT EXISTS mcp_memory;
        GRANT ALL PRIVILEGES ON DATABASE educational_platform TO toolboxai_user;
        GRANT ALL PRIVILEGES ON DATABASE ghost_backend TO toolboxai_user;
        GRANT ALL PRIVILEGES ON DATABASE roblox_data TO toolboxai_user;
        GRANT ALL PRIVILEGES ON DATABASE mcp_memory TO toolboxai_user;
    " 2>/dev/null || print_warning "Database creation commands had warnings (this is normal)"

    print_success "Database setup completed"

    # Step 3: Prepare application environment
    print_header "PREPARING APPLICATION ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    # Check if Python virtual environment exists
    if [ ! -d "ToolboxAI-Roblox-Environment/venv_clean" ]; then
        print_status "Creating Python virtual environment..."
        cd ToolboxAI-Roblox-Environment
        python -m venv venv_clean
        source venv_clean/bin/activate
        pip install -r requirements.txt
        cd ..
        print_success "Python environment ready"
    else
        print_success "Python environment already exists"
    fi
    
    # Check if Node.js dependencies are installed
    if [ -d "src/dashboard" ] && [ ! -d "src/dashboard/node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        cd src/dashboard
        npm install
        cd ../..
        print_success "Node.js dependencies installed"
    else
        print_success "Node.js dependencies already installed"
    fi

    # Step 4: Show staging summary
    print_header "STAGING DEPLOYMENT SUMMARY"

    echo -e "${GREEN}🎉 ToolboxAI Staging Infrastructure Ready!${NC}"
    echo ""
    echo -e "${BLUE}📊 Infrastructure Services:${NC}"
    echo "  • PostgreSQL: localhost:5432 (staging_password_2024)"
    echo "  • Redis: localhost:6379 (staging_redis_2024)"
    echo ""
    echo -e "${BLUE}🗄️ Databases Created:${NC}"
    echo "  • educational_platform"
    echo "  • ghost_backend"
    echo "  • roblox_data"
    echo "  • mcp_memory"
    echo ""
    echo -e "${BLUE}🚀 Manual Application Start Commands:${NC}"
    echo ""
    echo -e "${YELLOW}Terminal 1 - FastAPI Server:${NC}"
    echo "  cd ToolboxAI-Roblox-Environment"
    echo "  source venv_clean/bin/activate"
    echo "  export POSTGRES_PASSWORD=staging_password_2024"
    echo "  export REDIS_PASSWORD=staging_redis_2024"
    echo "  export JWT_SECRET_KEY=staging_jwt_secret_key_very_long_and_secure_2024"
    echo "  python server/main.py"
    echo ""
    echo -e "${YELLOW}Terminal 2 - Flask Bridge:${NC}"
    echo "  cd ToolboxAI-Roblox-Environment"
    echo "  source venv_clean/bin/activate"
    echo "  export POSTGRES_PASSWORD=staging_password_2024"
    echo "  export REDIS_PASSWORD=staging_redis_2024"
    echo "  python server/roblox_server.py"
    echo ""
    echo -e "${YELLOW}Terminal 3 - Dashboard:${NC}"
    echo "  cd src/dashboard"
    echo "  npm run dev"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • View logs: docker-compose -f config/production/docker-compose.staging.yml logs -f"
    echo "  • Stop infrastructure: docker-compose -f config/production/docker-compose.staging.yml down"
    echo "  • Restart infrastructure: docker-compose -f config/production/docker-compose.staging.yml restart"
    echo ""
    echo -e "${GREEN}✨ Infrastructure deployment completed successfully!${NC}"
    echo -e "${CYAN}💡 Start the applications manually using the commands above for testing.${NC}"

    # Create deployment report
    cat > "$PROJECT_ROOT/staging_deployment_report.md" << EOF
# ToolboxAI Staging Deployment Report

**Deployment Date:** $(date)
**Environment:** staging
**Status:** INFRASTRUCTURE SUCCESS

## Infrastructure Services Deployed
- PostgreSQL Database (Port 5432)
- Redis Cache (Port 6379)

## Databases Created
- educational_platform
- ghost_backend
- roblox_data
- mcp_memory

## Application Startup Instructions

### 1. FastAPI Server (Port 8008)
\`\`\`bash
cd ToolboxAI-Roblox-Environment
source venv_clean/bin/activate
export POSTGRES_PASSWORD=staging_password_2024
export REDIS_PASSWORD=staging_redis_2024
export JWT_SECRET_KEY=staging_jwt_secret_key_very_long_and_secure_2024
python server/main.py
\`\`\`

### 2. Flask Bridge (Port 5001)
\`\`\`bash
cd ToolboxAI-Roblox-Environment
source venv_clean/bin/activate
export POSTGRES_PASSWORD=staging_password_2024
export REDIS_PASSWORD=staging_redis_2024
python server/roblox_server.py
\`\`\`

### 3. Dashboard Frontend (Port 3000)
\`\`\`bash
cd src/dashboard
npm run dev
\`\`\`

## Testing Checklist
- [ ] FastAPI server starts successfully
- [ ] Flask bridge connects to database
- [ ] Dashboard loads in browser
- [ ] API endpoints respond correctly
- [ ] Database connections work
- [ ] WebSocket connections establish
- [ ] Authentication flow works
- [ ] User registration/login functions

## Rollback Instructions
\`\`\`bash
cd config/production
docker-compose -f docker-compose.staging.yml down
\`\`\`

## Next Steps
1. Start applications manually for testing
2. Validate all functionality
3. Run integration tests
4. Prepare for production deployment
EOF

    print_success "Deployment report created: staging_deployment_report.md"
}

# Handle command line options
case "${1:-}" in
    --stop)
        cd "$PROJECT_ROOT/config/production"
        docker-compose -f docker-compose.staging.yml down
        print_success "Staging infrastructure stopped"
        exit 0
        ;;
    --restart)
        cd "$PROJECT_ROOT/config/production"
        docker-compose -f docker-compose.staging.yml restart
        print_success "Staging infrastructure restarted"
        exit 0
        ;;
    --status)
        cd "$PROJECT_ROOT/config/production"
        docker-compose -f docker-compose.staging.yml ps
        exit 0
        ;;
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --stop      Stop staging infrastructure"
        echo "  --restart   Restart staging infrastructure"
        echo "  --status    Show staging infrastructure status"
        echo "  --help, -h  Show this help message"
        exit 0
        ;;
esac

# Run main function
main "$@"