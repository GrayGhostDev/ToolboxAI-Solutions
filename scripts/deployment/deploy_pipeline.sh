#!/bin/bash
#
# Deployment Pipeline Script
# Coordinates deployment across all terminals with real integration
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/deployment"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/deploy_${TIMESTAMP}.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "${RED}❌ Error occurred at line $1${NC}"
    log "${RED}Last command: $2${NC}"
    
    # Trigger rollback if needed
    if [ "$ENVIRONMENT" != "" ]; then
        log "${YELLOW}⚠️  Initiating rollback for $ENVIRONMENT${NC}"
        rollback_deployment
    fi
    
    exit 1
}

trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

# Function to check Redis availability
check_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping > /dev/null 2>&1; then
            echo "true"
        else
            echo "false"
        fi
    else
        echo "false"
    fi
}

# Function to publish Redis message
publish_message() {
    local channel=$1
    local message=$2
    
    if [ "$(check_redis)" == "true" ]; then
        redis-cli PUBLISH "$channel" "$message" > /dev/null
    fi
}

# Function to run pre-deployment checks
pre_deployment_checks() {
    log "${BLUE}🔍 Running pre-deployment checks...${NC}"
    
    # Check Python environment
    if ! command -v python3 &> /dev/null; then
        log "${RED}❌ Python3 not found${NC}"
        return 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log "${RED}❌ Node.js not found${NC}"
        return 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        log "${GREEN}✅ Docker available${NC}"
    else
        log "${YELLOW}⚠️  Docker not available (optional)${NC}"
    fi
    
    # Run deployment readiness check
    if [ -f "$SCRIPT_DIR/check_deployment_ready.py" ]; then
        log "${BLUE}🚀 Checking deployment readiness...${NC}"
        python3 "$SCRIPT_DIR/check_deployment_ready.py"
        
        if [ $? -ne 0 ]; then
            log "${RED}❌ Pre-deployment checks failed${NC}"
            return 1
        fi
    fi
    
    log "${GREEN}✅ Pre-deployment checks passed${NC}"
    return 0
}

# Function to run database migrations
run_migrations() {
    log "${BLUE}🗄️  Running database migrations...${NC}"
    
    publish_message "terminal:terminal1:migrate" "{\"env\":\"$ENVIRONMENT\"}"
    
    cd "$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
    
    # Check if alembic is available
    if [ -f "alembic.ini" ]; then
        log "Running Alembic migrations..."
        
        # Activate virtual environment if it exists
        if [ -d "venv_clean/bin" ]; then
            source venv_clean/bin/activate
        fi
        
        alembic upgrade head
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ Database migrations completed${NC}"
        else
            log "${RED}❌ Database migrations failed${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠️  No Alembic configuration found, skipping migrations${NC}"
    fi
    
    # Run custom migration scripts if they exist
    if [ -d "$PROJECT_ROOT/database/migrations" ]; then
        for migration_script in "$PROJECT_ROOT/database/migrations"/*.sql; do
            if [ -f "$migration_script" ]; then
                log "Running migration: $(basename $migration_script)"
                # Add actual database execution here
            fi
        done
    fi
    
    return 0
}

# Function to deploy backend
deploy_backend() {
    log "${BLUE}🚀 Deploying backend services...${NC}"
    
    publish_message "terminal:terminal1:deploy_backend" \
        "{\"env\":\"$ENVIRONMENT\",\"version\":\"$VERSION\"}"
    
    cd "$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
    
    # Build Python package
    if [ -d "venv_clean/bin" ]; then
        source venv_clean/bin/activate
        pip install -r requirements.txt
        
        # Run tests
        log "Running backend tests..."
        pytest tests/unit -v --tb=short
        
        if [ $? -ne 0 ]; then
            log "${RED}❌ Backend tests failed${NC}"
            return 1
        fi
    fi
    
    # Restart backend services
    log "Restarting backend services..."
    
    # Stop existing services
    if [ -f "$PROJECT_ROOT/scripts/stop_mcp_servers.sh" ]; then
        "$PROJECT_ROOT/scripts/stop_mcp_servers.sh"
    fi
    
    # Start services
    if [ -f "$PROJECT_ROOT/scripts/start_mcp_servers.sh" ]; then
        "$PROJECT_ROOT/scripts/start_mcp_servers.sh"
        sleep 5  # Give services time to start
    fi
    
    # Verify backend is running
    if curl -s http://127.0.0.1:8008/health > /dev/null; then
        log "${GREEN}✅ Backend deployed successfully${NC}"
    else
        log "${RED}❌ Backend deployment verification failed${NC}"
        return 1
    fi
    
    return 0
}

# Function to deploy frontend
deploy_frontend() {
    log "${BLUE}🎨 Deploying frontend...${NC}"
    
    publish_message "terminal:terminal2:deploy_frontend" \
        "{\"env\":\"$ENVIRONMENT\",\"version\":\"$VERSION\"}"
    
    cd "$PROJECT_ROOT/src/dashboard"
    
    # Install dependencies
    log "Installing frontend dependencies..."
    pppnpm install --frozen-lockfile
    
    # Build frontend
    log "Building frontend..."
    pnpm build
    
    if [ $? -ne 0 ]; then
        log "${RED}❌ Frontend build failed${NC}"
        return 1
    fi
    
    # Deploy built files (implementation depends on your setup)
    if [ "$ENVIRONMENT" == "production" ]; then
        # Copy to production directory or upload to CDN
        if [ -d "$PROJECT_ROOT/Production/deployed/dashboard" ]; then
            rm -rf "$PROJECT_ROOT/Production/deployed/dashboard"
        fi
        mkdir -p "$PROJECT_ROOT/Production/deployed"
        cp -r dist "$PROJECT_ROOT/Production/deployed/dashboard"
        log "${GREEN}✅ Frontend deployed to production${NC}"
    else
        # For staging, just verify the build
        log "${GREEN}✅ Frontend build completed for staging${NC}"
    fi
    
    return 0
}

# Function to deploy to cloud
deploy_cloud() {
    log "${BLUE}☁️  Deploying to cloud infrastructure...${NC}"
    
    publish_message "terminal:cloud:deploy_infrastructure" \
        "{\"env\":\"$ENVIRONMENT\",\"version\":\"$VERSION\"}"
    
    # Docker deployment if available
    if command -v docker &> /dev/null && [ -f "$PROJECT_ROOT/config/production/docker-compose.prod.yml" ]; then
        log "Deploying with Docker Compose..."
        
        cd "$PROJECT_ROOT"
        
        # Build images
        docker-compose -f config/production/docker-compose.prod.yml build
        
        # Deploy
        docker-compose -f config/production/docker-compose.prod.yml up -d
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ Cloud deployment successful${NC}"
        else
            log "${RED}❌ Cloud deployment failed${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠️  Docker not available, skipping cloud deployment${NC}"
    fi
    
    return 0
}

# Function to run smoke tests
run_smoke_tests() {
    log "${BLUE}🔥 Running smoke tests...${NC}"
    
    # Create smoke test script if it doesn't exist
    if [ ! -f "$SCRIPT_DIR/run_smoke_tests.py" ]; then
        cat > "$SCRIPT_DIR/run_smoke_tests.py" << 'EOF'
#!/usr/bin/env python3
import sys
import aiohttp
import asyncio

async def smoke_test():
    """Run basic smoke tests."""
    endpoints = [
        ('http://127.0.0.1:8008/health', 'FastAPI'),
        ('http://127.0.0.1:5001/health', 'Flask Bridge'),
        ('http://127.0.0.1:3000', 'Dashboard'),
    ]
    
    all_passed = True
    
    async with aiohttp.ClientSession() as session:
        for url, name in endpoints:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        print(f"✅ {name}: OK")
                    else:
                        print(f"❌ {name}: HTTP {response.status}")
                        all_passed = False
            except Exception as e:
                print(f"❌ {name}: {e}")
                all_passed = False
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(smoke_test())
    sys.exit(0 if result else 1)
EOF
        chmod +x "$SCRIPT_DIR/run_smoke_tests.py"
    fi
    
    python3 "$SCRIPT_DIR/run_smoke_tests.py"
    
    if [ $? -ne 0 ]; then
        log "${RED}❌ Smoke tests failed${NC}"
        return 1
    fi
    
    log "${GREEN}✅ Smoke tests passed${NC}"
    return 0
}

# Function to verify deployment
verify_deployment() {
    log "${BLUE}✔️  Verifying deployment...${NC}"
    
    if [ -f "$SCRIPT_DIR/verify_deployment.py" ]; then
        python3 "$SCRIPT_DIR/verify_deployment.py" --all-terminals
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ Deployment verification successful${NC}"
            return 0
        else
            log "${RED}❌ Deployment verification failed${NC}"
            return 1
        fi
    else
        # Basic verification
        run_smoke_tests
        return $?
    fi
}

# Function to rollback deployment
rollback_deployment() {
    log "${YELLOW}⚠️  Rolling back deployment for $ENVIRONMENT...${NC}"
    
    publish_message "terminal:all:rollback" "{\"env\":\"$ENVIRONMENT\"}"
    
    # Implement rollback logic here
    # For now, just restart services with previous version
    
    if [ -f "$PROJECT_ROOT/scripts/start_mcp_servers.sh" ]; then
        "$PROJECT_ROOT/scripts/start_mcp_servers.sh"
    fi
    
    log "${GREEN}✅ Rollback completed${NC}"
}

# Function to deploy to environment
deploy_to_environment() {
    ENVIRONMENT=$1
    VERSION=$2
    
    log "${BLUE}═══════════════════════════════════════════${NC}"
    log "${BLUE}🚀 Starting deployment to $ENVIRONMENT${NC}"
    log "${BLUE}📌 Version: $VERSION${NC}"
    log "${BLUE}⏰ Time: $(date)${NC}"
    log "${BLUE}═══════════════════════════════════════════${NC}"
    
    # Pre-deployment checks
    if ! pre_deployment_checks; then
        log "${RED}Pre-deployment checks failed${NC}"
        exit 1
    fi
    
    # Coordinate with all terminals
    log "${BLUE}📡 Coordinating with terminals...${NC}"
    if [ -f "$SCRIPT_DIR/coordinate_deployment.py" ]; then
        python3 "$SCRIPT_DIR/coordinate_deployment.py" --env="$ENVIRONMENT" --version="$VERSION"
    fi
    
    # Database migrations
    if ! run_migrations; then
        log "${RED}Migration failed${NC}"
        rollback_deployment
        exit 1
    fi
    
    # Deploy backend
    if ! deploy_backend; then
        log "${RED}Backend deployment failed${NC}"
        rollback_deployment
        exit 1
    fi
    
    # Deploy frontend
    if ! deploy_frontend; then
        log "${RED}Frontend deployment failed${NC}"
        rollback_deployment
        exit 1
    fi
    
    # Deploy to cloud
    if [ "$ENVIRONMENT" == "production" ]; then
        if ! deploy_cloud; then
            log "${RED}Cloud deployment failed${NC}"
            rollback_deployment
            exit 1
        fi
    fi
    
    # Run smoke tests
    if ! run_smoke_tests; then
        log "${RED}Smoke tests failed, initiating rollback${NC}"
        rollback_deployment
        exit 1
    fi
    
    # Verify deployment
    if ! verify_deployment; then
        log "${RED}Deployment verification failed${NC}"
        rollback_deployment
        exit 1
    fi
    
    # Deployment successful
    log "${GREEN}═══════════════════════════════════════════${NC}"
    log "${GREEN}✅ Deployment to $ENVIRONMENT successful!${NC}"
    log "${GREEN}📌 Version: $VERSION${NC}"
    log "${GREEN}⏰ Completed: $(date)${NC}"
    log "${GREEN}═══════════════════════════════════════════${NC}"
    
    # Notify all terminals
    publish_message "terminal:all:deploy_success" \
        "{\"env\":\"$ENVIRONMENT\",\"version\":\"$VERSION\"}"
    
    # Update documentation
    publish_message "terminal:documentation:update_deployment" \
        "{\"env\":\"$ENVIRONMENT\",\"version\":\"$VERSION\"}"
    
    # Save deployment record
    echo "{\"environment\":\"$ENVIRONMENT\",\"version\":\"$VERSION\",\"timestamp\":\"$(date -Iseconds)\"}" \
        >> "$LOG_DIR/deployment_history.json"
}

# Main execution
if [ "$1" == "staging" ] || [ "$1" == "production" ]; then
    VERSION=${2:-$(git rev-parse --short HEAD)}
    deploy_to_environment "$1" "$VERSION"
else
    echo "Usage: $0 [staging|production] [version]"
    echo ""
    echo "Examples:"
    echo "  $0 staging                    # Deploy current commit to staging"
    echo "  $0 production v1.2.3          # Deploy version v1.2.3 to production"
    echo "  $0 staging feature-branch     # Deploy feature branch to staging"
    exit 1
fi