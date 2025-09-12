#!/bin/bash

# ============================================================================
# ToolboxAI Integration Path Verification Script
# ============================================================================
# This script verifies all integration paths between services, databases,
# dashboard, and Roblox components to ensure proper communication.
#
# Usage: ./verify_integration_paths.sh [--verbose] [--fix-issues]
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
ROBLOX_ENV="$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
LOGS_DIR="$PROJECT_ROOT/logs"

# Service configurations
declare -A SERVICES=(
    ["fastapi_main"]="http://127.0.0.1:8008"
    ["dashboard_backend"]="http://127.0.0.1:8001"
    ["ghost_backend"]="http://127.0.0.1:8000"
    ["flask_bridge"]="http://127.0.0.1:5001"
    ["mcp_server"]="ws://127.0.0.1:9876"
)

# Database configurations
declare -A DATABASES=(
    ["educational_platform"]="localhost:5432"
    ["ghost_backend"]="localhost:5432"
    ["roblox_data"]="localhost:5432"
    ["mcp_memory"]="localhost:5432"
    ["toolboxai_dev"]="localhost:5432"
)

# Integration test results
declare -A INTEGRATION_RESULTS=()
VERBOSE=false
FIX_ISSUES=false

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

print_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${PURPLE}[VERBOSE]${NC} $1"
    fi
}

# Function to check service health
check_service_health() {
    local service_name="$1"
    local service_url="$2"
    local timeout=5

    print_verbose "Checking $service_name at $service_url"

    if [[ "$service_url" == ws://* ]]; then
        # WebSocket check
        if curl -s --connect-timeout $timeout "${service_url/http/ws}" >/dev/null 2>&1; then
            INTEGRATION_RESULTS["$service_name"]="healthy"
            print_success "$service_name: WebSocket connection successful"
            return 0
        else
            INTEGRATION_RESULTS["$service_name"]="unhealthy"
            print_error "$service_name: WebSocket connection failed"
            return 1
        fi
    else
        # HTTP check
        local health_endpoint="${service_url}/health"
        if curl -s --connect-timeout $timeout "$health_endpoint" >/dev/null 2>&1; then
            INTEGRATION_RESULTS["$service_name"]="healthy"
            print_success "$service_name: HTTP health check passed"
            return 0
        else
            # Try alternative endpoints
            local alt_endpoints=("/status" "/ping" "/")
            for endpoint in "${alt_endpoints[@]}"; do
                if curl -s --connect-timeout $timeout "${service_url}${endpoint}" >/dev/null 2>&1; then
                    INTEGRATION_RESULTS["$service_name"]="healthy"
                    print_success "$service_name: HTTP check passed at $endpoint"
                    return 0
                fi
            done

            INTEGRATION_RESULTS["$service_name"]="unhealthy"
            print_error "$service_name: HTTP health check failed"
            return 1
        fi
    fi
}

# Function to check database connectivity
check_database_connectivity() {
    local db_name="$1"
    local db_host_port="$2"

    print_verbose "Checking database connectivity for $db_name"

    # Extract host and port
    local host=$(echo "$db_host_port" | cut -d: -f1)
    local port=$(echo "$db_host_port" | cut -d: -f2)

    # Check if PostgreSQL is accessible
    if pg_isready -h "$host" -p "$port" >/dev/null 2>&1; then
        INTEGRATION_RESULTS["db_$db_name"]="healthy"
        print_success "Database $db_name: Connection successful"
        return 0
    else
        INTEGRATION_RESULTS["db_$db_name"]="unhealthy"
        print_error "Database $db_name: Connection failed"
        return 1
    fi
}

# Function to verify environment variables
verify_environment_variables() {
    print_header "VERIFYING ENVIRONMENT VARIABLES"

    local required_vars=(
        "EDU_DB_HOST" "EDU_DB_PORT" "EDU_DB_NAME" "EDU_DB_USER"
        "REDIS_HOST" "REDIS_PORT"
        "API_BASE_URL" "DASHBOARD_API_URL"
        "ROBLOX_API_URL" "MCP_HOST" "MCP_PORT"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
            print_error "Missing environment variable: $var"
        else
            print_verbose "Environment variable $var: ${!var}"
        fi
    done

    if [ ${#missing_vars[@]} -eq 0 ]; then
        INTEGRATION_RESULTS["env_vars"]="healthy"
        print_success "All required environment variables are set"
        return 0
    else
        INTEGRATION_RESULTS["env_vars"]="unhealthy"
        print_error "Missing ${#missing_vars[@]} environment variables"
        return 1
    fi
}

# Function to verify configuration files
verify_configuration_files() {
    print_header "VERIFYING CONFIGURATION FILES"

    local config_files=(
        "$PROJECT_ROOT/.env"
        "$PROJECT_ROOT/config/database.env"
        "$PROJECT_ROOT/config/mcp-servers.json"
        "$ROBLOX_ENV/requirements.txt"
        "$PROJECT_ROOT/pyproject.toml"
    )

    local missing_files=()

    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "Configuration file exists: $(basename "$file")"
        else
            missing_files+=("$file")
            print_error "Missing configuration file: $file"
        fi
    done

    if [ ${#missing_files[@]} -eq 0 ]; then
        INTEGRATION_RESULTS["config_files"]="healthy"
        print_success "All required configuration files exist"
        return 0
    else
        INTEGRATION_RESULTS["config_files"]="unhealthy"
        print_error "Missing ${#missing_files[@]} configuration files"
        return 1
    fi
}

# Function to verify API endpoints
verify_api_endpoints() {
    print_header "VERIFYING API ENDPOINTS"

    local endpoints=(
        "fastapi_main:/docs"
        "fastapi_main:/api/v1/health"
        "dashboard_backend:/api/health"
        "flask_bridge:/status"
    )

    local failed_endpoints=()

    for endpoint in "${endpoints[@]}"; do
        local service=$(echo "$endpoint" | cut -d: -f1)
        local path=$(echo "$endpoint" | cut -d: -f2)
        local url="${SERVICES[$service]}${path}"

        if curl -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
            print_success "API endpoint accessible: $service$path"
        else
            failed_endpoints+=("$service$path")
            print_error "API endpoint failed: $service$path"
        fi
    done

    if [ ${#failed_endpoints[@]} -eq 0 ]; then
        INTEGRATION_RESULTS["api_endpoints"]="healthy"
        print_success "All API endpoints are accessible"
        return 0
    else
        INTEGRATION_RESULTS["api_endpoints"]="unhealthy"
        print_error "Failed ${#failed_endpoints[@]} API endpoints"
        return 1
    fi
}

# Function to verify cross-service communication
verify_cross_service_communication() {
    print_header "VERIFYING CROSS-SERVICE COMMUNICATION"

    # Test dashboard -> backend communication
    print_status "Testing Dashboard -> Backend communication..."
    if curl -s --connect-timeout 5 "${SERVICES[dashboard_backend]}/api/health" >/dev/null 2>&1; then
        print_success "Dashboard can communicate with backend"
    else
        print_error "Dashboard cannot communicate with backend"
        INTEGRATION_RESULTS["dashboard_backend_comm"]="unhealthy"
        return 1
    fi

    # Test Roblox -> Flask Bridge communication
    print_status "Testing Roblox -> Flask Bridge communication..."
    if curl -s --connect-timeout 5 "${SERVICES[flask_bridge]}/status" >/dev/null 2>&1; then
        print_success "Roblox can communicate with Flask Bridge"
    else
        print_error "Roblox cannot communicate with Flask Bridge"
        INTEGRATION_RESULTS["roblox_flask_comm"]="unhealthy"
        return 1
    fi

    # Test MCP Server communication
    print_status "Testing MCP Server communication..."
    if curl -s --connect-timeout 5 "${SERVICES[mcp_server]/ws/http}" >/dev/null 2>&1; then
        print_success "MCP Server is accessible"
    else
        print_error "MCP Server is not accessible"
        INTEGRATION_RESULTS["mcp_server_comm"]="unhealthy"
        return 1
    fi

    INTEGRATION_RESULTS["cross_service_comm"]="healthy"
    print_success "Cross-service communication verified"
    return 0
}

# Function to verify file permissions
verify_file_permissions() {
    print_header "VERIFYING FILE PERMISSIONS"

    local critical_files=(
        "$SCRIPTS_DIR/start_mcp_servers.sh"
        "$SCRIPTS_DIR/stop_mcp_servers.sh"
        "$SCRIPTS_DIR/check_mcp_status.sh"
        "$SCRIPTS_DIR/setup_database.sh"
    )

    local permission_issues=()

    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            if [ -x "$file" ]; then
                print_success "File is executable: $(basename "$file")"
            else
                permission_issues+=("$file")
                print_error "File is not executable: $(basename "$file")"
            fi
        fi
    done

    if [ ${#permission_issues[@]} -eq 0 ]; then
        INTEGRATION_RESULTS["file_permissions"]="healthy"
        print_success "All critical files have proper permissions"
        return 0
    else
        INTEGRATION_RESULTS["file_permissions"]="unhealthy"
        print_error "Permission issues with ${#permission_issues[@]} files"
        return 1
    fi
}

# Function to generate integration report
generate_integration_report() {
    print_header "INTEGRATION VERIFICATION REPORT"

    local total_checks=${#INTEGRATION_RESULTS[@]}
    local healthy_checks=0
    local unhealthy_checks=0

    for check in "${!INTEGRATION_RESULTS[@]}"; do
        if [ "${INTEGRATION_RESULTS[$check]}" = "healthy" ]; then
            ((healthy_checks++))
        else
            ((unhealthy_checks++))
        fi
    done

    echo -e "${BLUE}📊 Integration Status Summary:${NC}"
    echo "  Total Checks: $total_checks"
    echo "  Healthy: $healthy_checks"
    echo "  Unhealthy: $unhealthy_checks"
    echo "  Success Rate: $(( healthy_checks * 100 / total_checks ))%"
    echo ""

    echo -e "${BLUE}📋 Detailed Results:${NC}"
    for check in "${!INTEGRATION_RESULTS[@]}"; do
        local status="${INTEGRATION_RESULTS[$check]}"
        local icon="✅"
        if [ "$status" = "unhealthy" ]; then
            icon="❌"
        fi
        echo "  $icon $check: $status"
    done

    echo ""
    if [ $unhealthy_checks -eq 0 ]; then
        print_success "🎉 All integration paths are healthy!"
        return 0
    else
        print_error "⚠️  $unhealthy_checks integration issues found"
        return 1
    fi
}

# Function to fix common issues
fix_common_issues() {
    if [ "$FIX_ISSUES" = true ]; then
        print_header "ATTEMPTING TO FIX COMMON ISSUES"

        # Fix file permissions
        print_status "Fixing file permissions..."
        chmod +x "$SCRIPTS_DIR"/*.sh 2>/dev/null || true

        # Create missing directories
        print_status "Creating missing directories..."
        mkdir -p "$LOGS_DIR" 2>/dev/null || true
        mkdir -p "$SCRIPTS_DIR/pids" 2>/dev/null || true

        # Create basic .env file if missing
        if [ ! -f "$PROJECT_ROOT/.env" ]; then
            print_status "Creating basic .env file..."
            cat > "$PROJECT_ROOT/.env" << 'EOF'
# Database Configuration
EDU_DB_HOST=localhost
EDU_DB_PORT=5432
EDU_DB_NAME=educational_platform
EDU_DB_USER=eduplatform
EDU_DB_PASSWORD=eduplatform2024

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
API_BASE_URL=http://127.0.0.1:8008
DASHBOARD_API_URL=http://127.0.0.1:8001
ROBLOX_API_URL=http://127.0.0.1:5001

# MCP Configuration
MCP_HOST=localhost
MCP_PORT=9876

# Environment
ENVIRONMENT=development
DEBUG=true
EOF
            print_success "Created basic .env file"
        fi

        print_success "Common issues fixed"
    fi
}

# Main execution function
main() {
    print_header "TOOLBOXAI INTEGRATION PATH VERIFICATION"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                VERBOSE=true
                shift
                ;;
            --fix-issues)
                FIX_ISSUES=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--verbose] [--fix-issues]"
                echo ""
                echo "Options:"
                echo "  --verbose     Show detailed output"
                echo "  --fix-issues  Attempt to fix common issues"
                echo "  --help, -h    Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run verification checks
    verify_environment_variables
    verify_configuration_files
    verify_file_permissions

    # Check service health
    print_header "CHECKING SERVICE HEALTH"
    for service in "${!SERVICES[@]}"; do
        check_service_health "$service" "${SERVICES[$service]}"
    done

    # Check database connectivity
    print_header "CHECKING DATABASE CONNECTIVITY"
    for db in "${!DATABASES[@]}"; do
        check_database_connectivity "$db" "${DATABASES[$db]}"
    done

    # Verify API endpoints
    verify_api_endpoints

    # Verify cross-service communication
    verify_cross_service_communication

    # Fix issues if requested
    fix_common_issues

    # Generate final report
    generate_integration_report

    # Exit with appropriate code
    local unhealthy_count=0
    for result in "${INTEGRATION_RESULTS[@]}"; do
        if [ "$result" = "unhealthy" ]; then
            ((unhealthy_count++))
        fi
    done

    if [ $unhealthy_count -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
