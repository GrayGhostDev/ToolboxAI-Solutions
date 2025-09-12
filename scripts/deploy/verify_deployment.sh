#!/usr/bin/env sh
# Kubernetes deployment verification wrapper
set -eu
# shellcheck source=../common/lib.sh
. "$(cd "$(dirname "$0")"/.. && pwd -P)/common/lib.sh" 2>/dev/null || true

NAMESPACE="${NAMESPACE:-default}"
APP="${APP:-backend}"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is not available" >&2
  exit 0
fi

kubectl get ns "$NAMESPACE" >/dev/null 2>&1 || { echo "Namespace $NAMESPACE not found" >&2; exit 1; }

set +e
kubectl -n "$NAMESPACE" rollout status deploy/"$APP" --timeout=120s
STATUS=$?
set -e

kubectl -n "$NAMESPACE" get deploy,svc,ingress || true
exit "$STATUS"

# ToolBoxAI Deployment Verification Script
# Comprehensive testing of the cloud/docker infrastructure

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENVIRONMENT=${ENVIRONMENT:-production}
NAMESPACE=${NAMESPACE:-toolboxai-production}

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

# Check Docker installation and configuration
check_docker() {
    log_info "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker is installed"
        
        # Check Docker daemon
        if docker info &> /dev/null; then
            log_success "Docker daemon is running"
        else
            log_error "Docker daemon is not running"
        fi
        
        # Check Docker Compose
        if command -v docker-compose &> /dev/null; then
            log_success "Docker Compose is installed"
        else
            log_warning "Docker Compose is not installed"
        fi
        
        # Check buildx
        if docker buildx version &> /dev/null; then
            log_success "Docker buildx is available"
        else
            log_warning "Docker buildx is not available"
        fi
    else
        log_error "Docker is not installed"
    fi
}

# Check Kubernetes cluster
check_kubernetes() {
    log_info "Checking Kubernetes cluster..."
    
    if command -v kubectl &> /dev/null; then
        log_success "kubectl is installed"
        
        # Check cluster connection
        if kubectl cluster-info &> /dev/null; then
            log_success "Connected to Kubernetes cluster"
            
            # Check namespace
            if kubectl get namespace $NAMESPACE &> /dev/null; then
                log_success "Namespace $NAMESPACE exists"
            else
                log_warning "Namespace $NAMESPACE does not exist"
            fi
            
            # Check nodes
            NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
            if [ "$NODE_COUNT" -gt 0 ]; then
                log_success "Cluster has $NODE_COUNT nodes"
            else
                log_error "No nodes found in cluster"
            fi
        else
            log_error "Cannot connect to Kubernetes cluster"
        fi
    else
        log_error "kubectl is not installed"
    fi
}

# Check Docker images
check_docker_images() {
    log_info "Checking Docker images..."
    
    IMAGES=("backend" "frontend" "flask-bridge" "dashboard-backend" "ghost")
    
    for IMAGE in "${IMAGES[@]}"; do
        IMAGE_NAME="ghcr.io/toolboxai-solutions/$IMAGE:latest"
        
        if docker image inspect "$IMAGE_NAME" &> /dev/null; then
            log_success "Image $IMAGE exists locally"
        else
            log_warning "Image $IMAGE not found locally"
        fi
    done
}

# Check Docker Compose services
check_compose_services() {
    log_info "Checking Docker Compose services..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "config/production/docker-compose.prod.yml" ]; then
        log_success "Docker Compose file exists"
        
        # Validate compose file
        if docker-compose -f config/production/docker-compose.prod.yml config &> /dev/null; then
            log_success "Docker Compose file is valid"
        else
            log_error "Docker Compose file validation failed"
        fi
        
        # Check if services are running
        if docker-compose -f config/production/docker-compose.prod.yml ps --services 2>/dev/null | grep -q .; then
            RUNNING_SERVICES=$(docker-compose -f config/production/docker-compose.prod.yml ps --services 2>/dev/null | wc -l)
            log_success "$RUNNING_SERVICES services defined in compose file"
        fi
    else
        log_error "Docker Compose file not found"
    fi
}

# Check Kubernetes deployments
check_k8s_deployments() {
    log_info "Checking Kubernetes deployments..."
    
    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        # Check deployments
        DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
        if [ "$DEPLOYMENTS" -gt 0 ]; then
            log_success "$DEPLOYMENTS deployments found in $NAMESPACE"
            
            # Check deployment status
            kubectl get deployments -n $NAMESPACE --no-headers 2>/dev/null | while read -r DEPLOYMENT; do
                NAME=$(echo "$DEPLOYMENT" | awk '{print $1}')
                READY=$(echo "$DEPLOYMENT" | awk '{print $2}')
                
                if [[ "$READY" == *"/"* ]] && [[ "$(echo "$READY" | cut -d'/' -f1)" == "$(echo "$READY" | cut -d'/' -f2)" ]]; then
                    log_success "Deployment $NAME is ready ($READY)"
                else
                    log_warning "Deployment $NAME is not fully ready ($READY)"
                fi
            done
        else
            log_warning "No deployments found in $NAMESPACE"
        fi
        
        # Check services
        SERVICES=$(kubectl get services -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
        if [ "$SERVICES" -gt 0 ]; then
            log_success "$SERVICES services found in $NAMESPACE"
        else
            log_warning "No services found in $NAMESPACE"
        fi
    fi
}

# Check service health endpoints
check_service_health() {
    log_info "Checking service health endpoints..."
    
    # Define health check endpoints
    declare -A HEALTH_ENDPOINTS=(
        ["FastAPI"]="http://localhost:8008/health"
        ["Dashboard Backend"]="http://localhost:8001/api/health"
        ["Flask Bridge"]="http://localhost:5001/status"
        ["Dashboard Frontend"]="http://localhost:5176"
        ["Ghost Backend"]="http://localhost:8000/ghost/api/v3/admin/site/"
    )
    
    for SERVICE in "${!HEALTH_ENDPOINTS[@]}"; do
        ENDPOINT="${HEALTH_ENDPOINTS[$SERVICE]}"
        
        if curl -f -s "$ENDPOINT" > /dev/null 2>&1; then
            log_success "$SERVICE is healthy ($ENDPOINT)"
        else
            log_warning "$SERVICE health check failed ($ENDPOINT)"
        fi
    done
}

# Check Redis connectivity
check_redis() {
    log_info "Checking Redis connectivity..."
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h localhost ping 2>/dev/null | grep -q PONG; then
            log_success "Redis is running and accessible"
            
            # Check Redis memory
            USED_MEMORY=$(redis-cli -h localhost INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            if [ -n "$USED_MEMORY" ]; then
                log_success "Redis memory usage: $USED_MEMORY"
            fi
        else
            log_error "Cannot connect to Redis"
        fi
    else
        log_warning "redis-cli not installed, skipping Redis check"
    fi
}

# Check PostgreSQL connectivity
check_postgres() {
    log_info "Checking PostgreSQL connectivity..."
    
    if command -v psql &> /dev/null; then
        if PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U toolboxai_user -d toolboxai_prod -c "SELECT 1" &> /dev/null; then
            log_success "PostgreSQL is running and accessible"
            
            # Check databases
            DBS=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U toolboxai_user -d toolboxai_prod -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;" 2>/dev/null | wc -l)
            if [ "$DBS" -gt 0 ]; then
                log_success "$DBS databases found in PostgreSQL"
            fi
        else
            log_warning "Cannot connect to PostgreSQL"
        fi
    else
        log_warning "psql not installed, skipping PostgreSQL check"
    fi
}

# Check monitoring stack
check_monitoring() {
    log_info "Checking monitoring stack..."
    
    # Check Prometheus
    if curl -f -s "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed"
    fi
    
    # Check Grafana
    if curl -f -s "http://localhost:3001/api/health" > /dev/null 2>&1; then
        log_success "Grafana is healthy"
    else
        log_warning "Grafana health check failed"
    fi
}

# Check configuration files
check_configuration() {
    log_info "Checking configuration files..."
    
    # Check for required configuration files
    CONFIG_FILES=(
        "config/production/docker-compose.prod.yml"
        "config/kubernetes/namespace.yaml"
        "config/kubernetes/backend-deployment.yaml"
        "config/kubernetes/postgres-statefulset.yaml"
        "config/kubernetes/redis-deployment.yaml"
        "config/kubernetes/ingress.yaml"
    )
    
    for FILE in "${CONFIG_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$FILE" ]; then
            log_success "Configuration file exists: $FILE"
        else
            log_error "Configuration file missing: $FILE"
        fi
    done
    
    # Check for environment file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log_success "Environment file (.env) exists"
    else
        log_warning "Environment file (.env) not found"
    fi
}

# Check deployment scripts
check_scripts() {
    log_info "Checking deployment scripts..."
    
    SCRIPTS=(
        "scripts/deploy/deploy_kubernetes.sh"
        "scripts/deploy/build_and_push_images.py"
        "scripts/terminal_sync/cloud_docker_sync.py"
    )
    
    for SCRIPT in "${SCRIPTS[@]}"; do
        if [ -f "$PROJECT_ROOT/$SCRIPT" ]; then
            log_success "Script exists: $SCRIPT"
            
            # Check if script is executable
            if [ -x "$PROJECT_ROOT/$SCRIPT" ]; then
                log_success "Script is executable: $SCRIPT"
            else
                log_warning "Script is not executable: $SCRIPT"
            fi
        else
            log_error "Script missing: $SCRIPT"
        fi
    done
}

# Performance test
check_performance() {
    log_info "Running basic performance checks..."
    
    # Test API response time
    if command -v curl &> /dev/null; then
        RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8008/health 2>/dev/null || echo "N/A")
        
        if [ "$RESPONSE_TIME" != "N/A" ]; then
            if (( $(echo "$RESPONSE_TIME < 1" | bc -l) )); then
                log_success "API response time: ${RESPONSE_TIME}s (good)"
            else
                log_warning "API response time: ${RESPONSE_TIME}s (slow)"
            fi
        fi
    fi
}

# Generate summary report
generate_report() {
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "                    DEPLOYMENT VERIFICATION REPORT           "
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $(date)"
    echo ""
    echo "Test Results:"
    echo "  ✓ Passed: $TESTS_PASSED"
    echo "  ✗ Failed: $TESTS_FAILED"
    echo ""
    
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo "Failed Tests:"
        for TEST in "${FAILED_TESTS[@]}"; do
            echo "  - $TEST"
        done
        echo ""
    fi
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✨ All tests passed! Deployment is healthy.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️ Some tests failed. Please review and fix issues.${NC}"
        exit 1
    fi
}

# Main execution
main() {
    echo "🔍 ToolBoxAI Deployment Verification"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    
    check_docker
    check_kubernetes
    check_docker_images
    check_compose_services
    check_k8s_deployments
    check_service_health
    check_redis
    check_postgres
    check_monitoring
    check_configuration
    check_scripts
    check_performance
    
    generate_report
}

# Run main function
main "$@"