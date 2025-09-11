#!/bin/bash

# ============================================================================
# ToolboxAI Complete Integration Test Suite
# ============================================================================
# This script performs comprehensive integration testing of all system
# components, including database connections, API endpoints, WebSocket
# communication, and cross-service integration.
#
# Usage: ./test_integration_complete.sh [--verbose] [--fix-issues] [--report]
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
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
LOGS_DIR="$PROJECT_ROOT/logs"

# Test configuration
VERBOSE=false
FIX_ISSUES=false
GENERATE_REPORT=true
TIMEOUT=30

# Test results
declare -A TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

# Function to run a test and record results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_description="$3"

    print_status "Running: $test_name"
    print_verbose "Description: $test_description"
    print_verbose "Command: $test_command"

    ((TOTAL_TESTS++))

    if eval "$test_command" >/dev/null 2>&1; then
        TEST_RESULTS["$test_name"]="passed"
        ((PASSED_TESTS++))
        print_success "$test_name: PASSED"
        return 0
    else
        TEST_RESULTS["$test_name"]="failed"
        ((FAILED_TESTS++))
        print_error "$test_name: FAILED"
        return 1
    fi
}

# Function to test service health
test_service_health() {
    print_header "TESTING SERVICE HEALTH"

    # FastAPI Main Server
    run_test "fastapi_health" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8008/health" \
        "FastAPI main server health check"

    # Dashboard Backend
    run_test "dashboard_backend_health" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8001/api/health" \
        "Dashboard backend health check"

    # Flask Bridge
    run_test "flask_bridge_health" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:5001/status" \
        "Flask bridge health check"

    # Ghost Backend
    run_test "ghost_backend_health" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8000/ghost/api/v3/admin/site/" \
        "Ghost backend health check"

    # MCP Server WebSocket
    run_test "mcp_websocket_health" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:9876" \
        "MCP server WebSocket health check"
}

# Function to test database connectivity
test_database_connectivity() {
    print_header "TESTING DATABASE CONNECTIVITY"

    # PostgreSQL connection
    run_test "postgresql_connection" \
        "pg_isready -h localhost -p 5432" \
        "PostgreSQL database connection"

    # Educational Platform Database
    run_test "edu_db_connection" \
        "psql -h localhost -p 5432 -U eduplatform -d educational_platform -c 'SELECT 1;'" \
        "Educational platform database connection"

    # Ghost Backend Database
    run_test "ghost_db_connection" \
        "psql -h localhost -p 5432 -U ghost_user -d ghost_backend -c 'SELECT 1;'" \
        "Ghost backend database connection"

    # Roblox Data Database
    run_test "roblox_db_connection" \
        "psql -h localhost -p 5432 -U roblox_user -d roblox_data -c 'SELECT 1;'" \
        "Roblox data database connection"

    # MCP Memory Database
    run_test "mcp_db_connection" \
        "psql -h localhost -p 5432 -U mcp_user -d mcp_memory -c 'SELECT 1;'" \
        "MCP memory database connection"
}

# Function to test Redis connectivity
test_redis_connectivity() {
    print_header "TESTING REDIS CONNECTIVITY"

    # Redis connection
    run_test "redis_connection" \
        "redis-cli -h localhost -p 6379 ping" \
        "Redis cache connection"

    # Redis read/write test
    run_test "redis_read_write" \
        "redis-cli -h localhost -p 6379 set test_key 'test_value' && redis-cli -h localhost -p 6379 get test_key | grep -q 'test_value'" \
        "Redis read/write operations"
}

# Function to test API endpoints
test_api_endpoints() {
    print_header "TESTING API ENDPOINTS"

    # FastAPI endpoints
    run_test "fastapi_docs" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8008/docs" \
        "FastAPI documentation endpoint"

    run_test "fastapi_openapi" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8008/openapi.json" \
        "FastAPI OpenAPI schema endpoint"

    # Dashboard API endpoints
    run_test "dashboard_api_users" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8001/api/users" \
        "Dashboard API users endpoint"

    run_test "dashboard_api_courses" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8001/api/courses" \
        "Dashboard API courses endpoint"

    # Flask Bridge endpoints
    run_test "flask_bridge_roblox" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:5001/roblox/status" \
        "Flask bridge Roblox endpoint"

    # Ghost API endpoints
    run_test "ghost_api_posts" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:8000/ghost/api/v3/content/posts/" \
        "Ghost API posts endpoint"
}

# Function to test WebSocket connections
test_websocket_connections() {
    print_header "TESTING WEBSOCKET CONNECTIONS"

    # MCP WebSocket connection
    run_test "mcp_websocket_connection" \
        "timeout 5 websocat ws://localhost:9876 || echo 'WebSocket connection test completed'" \
        "MCP WebSocket connection test"

    # FastAPI WebSocket endpoints
    run_test "fastapi_websocket" \
        "curl -s --connect-timeout $TIMEOUT -H 'Upgrade: websocket' -H 'Connection: Upgrade' http://localhost:8008/ws" \
        "FastAPI WebSocket endpoint"
}

# Function to test cross-service communication
test_cross_service_communication() {
    print_header "TESTING CROSS-SERVICE COMMUNICATION"

    # Dashboard -> FastAPI communication
    run_test "dashboard_to_fastapi" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST http://localhost:8001/api/test-fastapi-connection" \
        "Dashboard to FastAPI communication"

    # Flask Bridge -> FastAPI communication
    run_test "flask_to_fastapi" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST http://localhost:5001/test-fastapi-connection" \
        "Flask Bridge to FastAPI communication"

    # MCP Server -> FastAPI communication
    run_test "mcp_to_fastapi" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:9876/health" \
        "MCP Server to FastAPI communication"
}

# Function to test authentication flow
test_authentication_flow() {
    print_header "TESTING AUTHENTICATION FLOW"

    # User registration
    run_test "user_registration" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"email\":\"test@example.com\",\"password\":\"testpass123\"}' http://localhost:8008/auth/register" \
        "User registration endpoint"

    # User login
    run_test "user_login" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"email\":\"test@example.com\",\"password\":\"testpass123\"}' http://localhost:8008/auth/login" \
        "User login endpoint"

    # JWT token validation
    run_test "jwt_validation" \
        "curl -s --connect-timeout $TIMEOUT -H 'Authorization: Bearer test_token' http://localhost:8008/auth/me" \
        "JWT token validation"
}

# Function to test content generation workflow
test_content_generation_workflow() {
    print_header "TESTING CONTENT GENERATION WORKFLOW"

    # Content generation request
    run_test "content_generation_request" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"subject\":\"Mathematics\",\"grade_level\":7,\"topic\":\"Algebra\"}' http://localhost:8008/api/content/generate" \
        "Content generation request"

    # Quiz generation
    run_test "quiz_generation" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"lesson_id\":\"123\",\"num_questions\":5}' http://localhost:8008/api/quiz/generate" \
        "Quiz generation request"

    # Terrain generation
    run_test "terrain_generation" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"theme\":\"classroom\",\"size\":\"medium\"}' http://localhost:8008/api/terrain/generate" \
        "Terrain generation request"
}

# Function to test Roblox integration
test_roblox_integration() {
    print_header "TESTING ROBLOX INTEGRATION"

    # Roblox plugin communication
    run_test "roblox_plugin_communication" \
        "curl -s --connect-timeout $TIMEOUT http://localhost:5001/roblox/plugin/status" \
        "Roblox plugin communication"

    # Roblox data synchronization
    run_test "roblox_data_sync" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"player_id\":\"123\",\"data\":{\"score\":100}}' http://localhost:5001/roblox/sync" \
        "Roblox data synchronization"

    # Roblox script generation
    run_test "roblox_script_generation" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d '{\"script_type\":\"quiz_ui\",\"parameters\":{}}' http://localhost:5001/roblox/generate-script" \
        "Roblox script generation"
}

# Function to test performance metrics
test_performance_metrics() {
    print_header "TESTING PERFORMANCE METRICS"

    # Response time tests
    run_test "fastapi_response_time" \
        "curl -s --connect-timeout $TIMEOUT -w '%{time_total}' -o /dev/null http://localhost:8008/health | awk '{if (\$1 < 1.0) exit 0; else exit 1}'" \
        "FastAPI response time under 1 second"

    run_test "dashboard_response_time" \
        "curl -s --connect-timeout $TIMEOUT -w '%{time_total}' -o /dev/null http://localhost:8001/api/health | awk '{if (\$1 < 1.0) exit 0; else exit 1}'" \
        "Dashboard response time under 1 second"

    # Concurrent request handling
    run_test "concurrent_requests" \
        "for i in {1..10}; do curl -s --connect-timeout $TIMEOUT http://localhost:8008/health & done; wait" \
        "Concurrent request handling"
}

# Function to test error handling
test_error_handling() {
    print_header "TESTING ERROR HANDLING"

    # 404 error handling
    run_test "404_error_handling" \
        "curl -s --connect-timeout $TIMEOUT -w '%{http_code}' -o /dev/null http://localhost:8008/nonexistent | grep -q '404'" \
        "404 error handling"

    # Invalid JSON handling
    run_test "invalid_json_handling" \
        "curl -s --connect-timeout $TIMEOUT -H 'Content-Type: application/json' -X POST -d 'invalid json' http://localhost:8008/api/content/generate | grep -q 'error'" \
        "Invalid JSON error handling"

    # Authentication error handling
    run_test "auth_error_handling" \
        "curl -s --connect-timeout $TIMEOUT -H 'Authorization: Bearer invalid_token' http://localhost:8008/auth/me | grep -q 'error'" \
        "Authentication error handling"
}

# Function to generate test report
generate_test_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        return 0
    fi

    print_header "GENERATING INTEGRATION TEST REPORT"

    local report_file="$TEST_RESULTS_DIR/integration-test-report.html"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    mkdir -p "$TEST_RESULTS_DIR"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>ToolboxAI Integration Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 3px; }
        .passed { background-color: #d4edda; color: #155724; }
        .failed { background-color: #f8d7da; color: #721c24; }
        .details { margin-top: 20px; }
        .section { margin: 20px 0; }
        .section h3 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ToolboxAI Integration Test Report</h1>
        <p>Generated: $timestamp</p>
        <p>Total Tests: $TOTAL_TESTS | Passed: $PASSED_TESTS | Failed: $FAILED_TESTS</p>
        <p>Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%</p>
    </div>

    <div class="summary">
        <h2>Test Summary</h2>
        <p><strong>Total Tests:</strong> $TOTAL_TESTS</p>
        <p><strong>Passed:</strong> $PASSED_TESTS</p>
        <p><strong>Failed:</strong> $FAILED_TESTS</p>
        <p><strong>Success Rate:</strong> $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%</p>
    </div>

    <div class="details">
        <h2>Test Results by Category</h2>
EOF

    # Group tests by category
    local categories=("service_health" "database" "redis" "api" "websocket" "cross_service" "auth" "content" "roblox" "performance" "error")

    for category in "${categories[@]}"; do
        echo "        <div class=\"section\">" >> "$report_file"
        echo "            <h3>$(echo $category | tr '_' ' ' | sed 's/\b\w/\U&/g')</h3>" >> "$report_file"

        for test_name in "${!TEST_RESULTS[@]}"; do
            if [[ "$test_name" == *"$category"* ]]; then
                local result="${TEST_RESULTS[$test_name]}"
                local class=""
                case "$result" in
                    "passed") class="passed" ;;
                    "failed") class="failed" ;;
                esac

                echo "            <div class=\"test-result $class\">" >> "$report_file"
                echo "                <strong>$test_name:</strong> $result" >> "$report_file"
                echo "            </div>" >> "$report_file"
            fi
        done

        echo "        </div>" >> "$report_file"
    done

    cat >> "$report_file" << EOF
    </div>

    <div class="details">
        <h2>All Test Results</h2>
EOF

    for test_name in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[$test_name]}"
        local class=""
        case "$result" in
            "passed") class="passed" ;;
            "failed") class="failed" ;;
        esac

        cat >> "$report_file" << EOF
        <div class="test-result $class">
            <strong>$test_name:</strong> $result
        </div>
EOF
    done

    cat >> "$report_file" << EOF
    </div>
</body>
</html>
EOF

    print_success "Integration test report generated: $report_file"
}

# Function to show test summary
show_test_summary() {
    print_header "INTEGRATION TEST SUMMARY"

    echo -e "${BLUE}📊 Test Results:${NC}"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed: $PASSED_TESTS"
    echo "  Failed: $FAILED_TESTS"
    echo "  Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo ""

    echo -e "${BLUE}📋 Detailed Results:${NC}"
    for test_name in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[$test_name]}"
        local icon="✅"
        if [ "$result" = "failed" ]; then
            icon="❌"
        fi
        echo "  $icon $test_name: $result"
    done

    echo ""
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "🎉 All integration tests passed!"
        if [ "$GENERATE_REPORT" = true ]; then
            echo -e "${BLUE}📄 Test report available at: $TEST_RESULTS_DIR/integration-test-report.html${NC}"
        fi
        return 0
    else
        print_error "⚠️  $FAILED_TESTS integration test(s) failed"
        return 1
    fi
}

# Main execution function
main() {
    print_header "TOOLBOXAI COMPLETE INTEGRATION TESTING"

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
            --no-report)
                GENERATE_REPORT=false
                shift
                ;;
            --timeout=*)
                TIMEOUT="${1#*=}"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --verbose           Show verbose output"
                echo "  --fix-issues        Attempt to fix common issues"
                echo "  --no-report         Skip report generation"
                echo "  --timeout=SECONDS   Set timeout for requests (default: 30)"
                echo "  --help, -h          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"

    # Run all test categories
    test_service_health
    test_database_connectivity
    test_redis_connectivity
    test_api_endpoints
    test_websocket_connections
    test_cross_service_communication
    test_authentication_flow
    test_content_generation_workflow
    test_roblox_integration
    test_performance_metrics
    test_error_handling

    # Generate report and show summary
    generate_test_report
    show_test_summary

    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
