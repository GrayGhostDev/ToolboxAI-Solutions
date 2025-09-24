#!/bin/bash
# Docker Setup Validation Script for ToolBoxAI Dashboard
# Validates the Docker configuration and runs comprehensive tests

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

# Test configuration
TIMEOUT=30
SERVICES=(
    "postgres"
    "redis"
    "fastapi-main"
    "dashboard-frontend"
)

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

# Test results tracking
declare -A test_results
total_tests=0
passed_tests=0
failed_tests=0

# Function to record test result
record_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    total_tests=$((total_tests + 1))
    test_results["$test_name"]="$result"

    if [ "$result" = "PASS" ]; then
        passed_tests=$((passed_tests + 1))
        log_success "✅ $test_name: $message"
    else
        failed_tests=$((failed_tests + 1))
        log_error "❌ $test_name: $message"
    fi
}

# Function to validate prerequisites
validate_prerequisites() {
    log_info "🔍 Validating prerequisites..."

    # Check Docker
    if command -v docker &> /dev/null; then
        record_test "Docker Installation" "PASS" "Docker is installed and accessible"
    else
        record_test "Docker Installation" "FAIL" "Docker is not installed or not in PATH"
        return 1
    fi

    # Check Docker Compose
    if docker compose version &> /dev/null; then
        record_test "Docker Compose" "PASS" "Docker Compose is available"
    else
        record_test "Docker Compose" "FAIL" "Docker Compose is not available"
        return 1
    fi

    # Check compose file
    if [ -f "$DOCKER_DIR/$COMPOSE_FILE" ]; then
        record_test "Compose File" "PASS" "docker-compose.dev.yml exists"
    else
        record_test "Compose File" "FAIL" "docker-compose.dev.yml not found"
        return 1
    fi

    # Check Dockerfiles
    if [ -f "$DOCKER_DIR/dashboard.dev.Dockerfile" ]; then
        record_test "Development Dockerfile" "PASS" "dashboard.dev.Dockerfile exists"
    else
        record_test "Development Dockerfile" "FAIL" "dashboard.dev.Dockerfile not found"
        return 1
    fi

    # Check entrypoint script
    if [ -f "$DOCKER_DIR/docker-entrypoint.sh" ] && [ -x "$DOCKER_DIR/docker-entrypoint.sh" ]; then
        record_test "Entrypoint Script" "PASS" "docker-entrypoint.sh exists and is executable"
    else
        record_test "Entrypoint Script" "FAIL" "docker-entrypoint.sh missing or not executable"
        return 1
    fi
}

# Function to validate Docker Compose configuration
validate_compose_config() {
    log_info "🔧 Validating Docker Compose configuration..."

    cd "$DOCKER_DIR"

    # Check compose file syntax
    if docker compose -f "$COMPOSE_FILE" config &> /dev/null; then
        record_test "Compose Syntax" "PASS" "docker-compose.dev.yml syntax is valid"
    else
        record_test "Compose Syntax" "FAIL" "docker-compose.dev.yml has syntax errors"
        return 1
    fi

    # Check for required services
    for service in "${SERVICES[@]}"; do
        if docker compose -f "$COMPOSE_FILE" config --services | grep -q "^${service}$"; then
            record_test "Service Definition: $service" "PASS" "Service $service is defined"
        else
            record_test "Service Definition: $service" "FAIL" "Service $service is not defined"
        fi
    done
}

# Function to validate environment variables
validate_environment() {
    log_info "🌍 Validating environment variables..."

    # Check for .env file
    if [ -f "$PROJECT_DIR/.env" ]; then
        record_test "Environment File" "PASS" ".env file exists"

        # Source the environment file
        source "$PROJECT_DIR/.env"
    else
        record_test "Environment File" "WARN" ".env file not found (using defaults)"
    fi

    # Check critical environment variables
    local critical_vars=(
        "POSTGRES_PASSWORD"
        "JWT_SECRET_KEY"
    )

    for var in "${critical_vars[@]}"; do
        if [ -n "${!var}" ]; then
            record_test "Environment Variable: $var" "PASS" "$var is set"
        else
            record_test "Environment Variable: $var" "FAIL" "$var is not set"
        fi
    done

    # Check optional but important variables
    local important_vars=(
        "PUSHER_KEY"
        "PUSHER_SECRET"
        "OPENAI_API_KEY"
    )

    for var in "${important_vars[@]}"; do
        if [ -n "${!var}" ]; then
            record_test "Optional Variable: $var" "PASS" "$var is set"
        else
            record_test "Optional Variable: $var" "WARN" "$var is not set (optional)"
        fi
    done
}

# Function to test Docker image builds
test_image_builds() {
    log_info "🏗️ Testing Docker image builds..."

    cd "$DOCKER_DIR"

    # Test dashboard development build
    if docker compose -f "$COMPOSE_FILE" build dashboard-frontend &> /tmp/build.log; then
        record_test "Dashboard Build" "PASS" "Dashboard development image builds successfully"
    else
        record_test "Dashboard Build" "FAIL" "Dashboard development image build failed"
        log_error "Build log:"
        cat /tmp/build.log | tail -20
    fi

    # Test production build
    if docker build -f dashboard.Dockerfile --build-arg VITE_API_BASE_URL=http://localhost:8009/api/v1 ../.. -t dashboard-prod-test &> /tmp/build-prod.log; then
        record_test "Production Build" "PASS" "Dashboard production image builds successfully"
    else
        record_test "Production Build" "FAIL" "Dashboard production image build failed"
        log_error "Production build log:"
        cat /tmp/build-prod.log | tail -20
    fi
}

# Function to test service startup
test_service_startup() {
    log_info "🚀 Testing service startup..."

    cd "$DOCKER_DIR"

    # Start infrastructure services first
    docker compose -f "$COMPOSE_FILE" up -d postgres redis &> /dev/null

    # Wait for infrastructure to be healthy
    for service in "postgres" "redis"; do
        local attempts=0
        local max_attempts=30

        while [ $attempts -lt $max_attempts ]; do
            if docker compose -f "$COMPOSE_FILE" ps "$service" --format "{{.Health}}" | grep -q "healthy"; then
                record_test "Service Startup: $service" "PASS" "$service started and is healthy"
                break
            fi

            attempts=$((attempts + 1))
            sleep 2
        done

        if [ $attempts -eq $max_attempts ]; then
            record_test "Service Startup: $service" "FAIL" "$service failed to become healthy"
        fi
    done

    # Start backend services
    docker compose -f "$COMPOSE_FILE" up -d fastapi-main &> /dev/null

    # Wait for backend to be ready
    local attempts=0
    local max_attempts=60

    while [ $attempts -lt $max_attempts ]; do
        if curl -f -s http://localhost:8009/health &> /dev/null; then
            record_test "Backend API" "PASS" "FastAPI backend is responding"
            break
        fi

        attempts=$((attempts + 1))
        sleep 2
    done

    if [ $attempts -eq $max_attempts ]; then
        record_test "Backend API" "FAIL" "FastAPI backend is not responding"
    fi

    # Start dashboard frontend
    docker compose -f "$COMPOSE_FILE" up -d dashboard-frontend &> /dev/null

    # Wait for frontend to be ready
    attempts=0
    max_attempts=60

    while [ $attempts -lt $max_attempts ]; do
        if curl -f -s http://localhost:5179/ &> /dev/null; then
            record_test "Frontend Service" "PASS" "Dashboard frontend is serving content"
            break
        fi

        attempts=$((attempts + 1))
        sleep 2
    done

    if [ $attempts -eq $max_attempts ]; then
        record_test "Frontend Service" "FAIL" "Dashboard frontend is not responding"
    fi
}

# Function to test health endpoints
test_health_endpoints() {
    log_info "🏥 Testing health endpoints..."

    # Test backend health
    if curl -f -s http://localhost:8009/health &> /dev/null; then
        record_test "Backend Health" "PASS" "Backend health endpoint responds"
    else
        record_test "Backend Health" "FAIL" "Backend health endpoint not responding"
    fi

    # Test frontend health
    if curl -f -s http://localhost:5179/health &> /dev/null; then
        record_test "Frontend Health" "PASS" "Frontend health endpoint responds"
    else
        record_test "Frontend Health" "FAIL" "Frontend health endpoint not responding"
    fi

    # Test API connectivity
    if curl -f -s http://localhost:5179/api/health &> /dev/null; then
        record_test "API Proxy" "PASS" "API proxy is working"
    else
        record_test "API Proxy" "FAIL" "API proxy is not working"
    fi
}

# Function to test container networking
test_networking() {
    log_info "🌐 Testing container networking..."

    # Test inter-container communication
    if docker compose -f "$COMPOSE_FILE" exec -T dashboard-frontend curl -f -s http://fastapi-main:8009/health &> /dev/null; then
        record_test "Inter-Container Communication" "PASS" "Frontend can reach backend"
    else
        record_test "Inter-Container Communication" "FAIL" "Frontend cannot reach backend"
    fi

    # Test database connectivity from backend
    if docker compose -f "$COMPOSE_FILE" exec -T fastapi-main nc -z postgres 5432 &> /dev/null; then
        record_test "Database Connectivity" "PASS" "Backend can reach database"
    else
        record_test "Database Connectivity" "FAIL" "Backend cannot reach database"
    fi

    # Test Redis connectivity
    if docker compose -f "$COMPOSE_FILE" exec -T fastapi-main nc -z redis 6379 &> /dev/null; then
        record_test "Redis Connectivity" "PASS" "Backend can reach Redis"
    else
        record_test "Redis Connectivity" "FAIL" "Backend cannot reach Redis"
    fi
}

# Function to cleanup test environment
cleanup() {
    log_info "🧹 Cleaning up test environment..."

    cd "$DOCKER_DIR"
    docker compose -f "$COMPOSE_FILE" down --remove-orphans &> /dev/null || true
    docker rmi dashboard-prod-test &> /dev/null || true

    # Clean up temporary files
    rm -f /tmp/build.log /tmp/build-prod.log
}

# Function to generate test report
generate_report() {
    echo
    log_info "📊 Test Report Summary"
    echo "=================================================="
    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $failed_tests"
    echo "Success Rate: $(( (passed_tests * 100) / total_tests ))%"
    echo

    if [ $failed_tests -gt 0 ]; then
        log_error "❌ Some tests failed. Please review the issues above."
        echo
        log_info "💡 Troubleshooting Tips:"
        echo "1. Check that all required environment variables are set"
        echo "2. Ensure no other services are using ports 5179, 8009, 5434, 6381"
        echo "3. Verify Docker daemon is running and accessible"
        echo "4. Check Docker Compose version compatibility"
        echo "5. Review service logs: docker-compose -f docker-compose.dev.yml logs [service]"
        return 1
    else
        log_success "🎉 All tests passed! Docker setup is ready for development."
        return 0
    fi
}

# Main execution
main() {
    log_info "============================================"
    log_info "🧪 ToolBoxAI Docker Setup Validation"
    log_info "============================================"

    # Trap to ensure cleanup on exit
    trap cleanup EXIT

    # Run validation steps
    validate_prerequisites || exit 1
    validate_compose_config || exit 1
    validate_environment
    test_image_builds
    test_service_startup
    test_health_endpoints
    test_networking

    # Generate final report
    generate_report
}

# Show usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Docker setup validation script for ToolBoxAI Dashboard

Options:
    -h, --help      Show this help message
    --skip-build    Skip Docker image build tests
    --skip-startup  Skip service startup tests
    --cleanup-only  Only run cleanup (useful for manual cleanup)

Examples:
    $0                  # Run all validation tests
    $0 --skip-build     # Skip build tests (faster)
    $0 --cleanup-only   # Only cleanup test environment

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-startup)
            SKIP_STARTUP=true
            shift
            ;;
        --cleanup-only)
            cleanup
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Execute main function if script is run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi