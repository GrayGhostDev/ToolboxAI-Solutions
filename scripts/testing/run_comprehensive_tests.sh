#!/bin/bash

# ============================================================================
# ToolboxAI Comprehensive Testing Script
# ============================================================================
# This script runs all tests including unit, integration, e2e, and performance
# tests for the complete ToolboxAI platform. It integrates with the existing
# test structure and provides detailed reporting.
#
# Usage: ./run_comprehensive_tests.sh [--type=all|unit|integration|e2e|performance] [--verbose] [--coverage]
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
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"

# Test configuration
TEST_TYPE="all"
VERBOSE=false
COVERAGE=false
PARALLEL=false
FAIL_FAST=false
GENERATE_REPORT=true

# Test results
declare -A TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

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

# Function to check prerequisites
check_prerequisites() {
    print_header "CHECKING TEST PREREQUISITES"

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    print_success "Python 3 is available"

    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        print_warning "pytest is not installed, installing..."
        pip3 install pytest pytest-asyncio pytest-cov pytest-html
    fi

    print_success "pytest is available"

    # Check if required test directories exist
    local test_dirs=(
        "$ROBLOX_ENV/tests"
        "$ROBLOX_ENV/tests/unit"
        "$ROBLOX_ENV/tests/integration"
        "$ROBLOX_ENV/tests/e2e"
        "$ROBLOX_ENV/tests/performance"
    )

    for dir in "${test_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Test directory exists: $(basename "$dir")"
        else
            print_warning "Test directory missing: $dir"
        fi
    done

    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"

    print_success "Test prerequisites checked"
}

# Function to run unit tests
run_unit_tests() {
    print_header "RUNNING UNIT TESTS"

    local unit_test_dir="$ROBLOX_ENV/tests/unit"
    local test_args=()

    if [ "$VERBOSE" = true ]; then
        test_args+=("-v")
    fi

    if [ "$COVERAGE" = true ]; then
        test_args+=("--cov=src" "--cov-report=html:$TEST_RESULTS_DIR/coverage-unit" "--cov-report=term")
    fi

    if [ "$FAIL_FAST" = true ]; then
        test_args+=("-x")
    fi

    test_args+=("--html=$TEST_RESULTS_DIR/unit-test-report.html" "--self-contained-html")

    if [ -d "$unit_test_dir" ]; then
        print_status "Running unit tests from $unit_test_dir..."

        cd "$ROBLOX_ENV"
        if pytest "${test_args[@]}" "$unit_test_dir"; then
            TEST_RESULTS["unit"]="passed"
            print_success "Unit tests passed"
        else
            TEST_RESULTS["unit"]="failed"
            print_error "Unit tests failed"
            return 1
        fi
    else
        print_warning "Unit test directory not found, skipping unit tests"
        TEST_RESULTS["unit"]="skipped"
    fi

    return 0
}

# Function to run integration tests
run_integration_tests() {
    print_header "RUNNING INTEGRATION TESTS"

    local integration_test_dir="$ROBLOX_ENV/tests/integration"
    local test_args=()

    if [ "$VERBOSE" = true ]; then
        test_args+=("-v")
    fi

    if [ "$COVERAGE" = true ]; then
        test_args+=("--cov=src" "--cov-report=html:$TEST_RESULTS_DIR/coverage-integration" "--cov-report=term")
    fi

    if [ "$FAIL_FAST" = true ]; then
        test_args+=("-x")
    fi

    test_args+=("--html=$TEST_RESULTS_DIR/integration-test-report.html" "--self-contained-html")

    if [ -d "$integration_test_dir" ]; then
        print_status "Running integration tests from $integration_test_dir..."

        cd "$ROBLOX_ENV"
        if pytest "${test_args[@]}" "$integration_test_dir"; then
            TEST_RESULTS["integration"]="passed"
            print_success "Integration tests passed"
        else
            TEST_RESULTS["integration"]="failed"
            print_error "Integration tests failed"
            return 1
        fi
    else
        print_warning "Integration test directory not found, skipping integration tests"
        TEST_RESULTS["integration"]="skipped"
    fi

    return 0
}

# Function to run end-to-end tests
run_e2e_tests() {
    print_header "RUNNING END-TO-END TESTS"

    local e2e_test_dir="$ROBLOX_ENV/tests/e2e"
    local e2e_test_files=(
        "$ROBLOX_ENV/tests/test_e2e_integration.py"
        "$ROBLOX_ENV/tests/test_full_integration.py"
    )

    local test_args=()

    if [ "$VERBOSE" = true ]; then
        test_args+=("-v")
    fi

    if [ "$FAIL_FAST" = true ]; then
        test_args+=("-x")
    fi

    test_args+=("--html=$TEST_RESULTS_DIR/e2e-test-report.html" "--self-contained-html")

    # Check if services are running
    print_status "Checking if services are running..."
    local services_running=0

    if curl -s --connect-timeout 5 "http://localhost:8008/health" >/dev/null 2>&1; then
        ((services_running++))
        print_success "FastAPI server is running"
    else
        print_warning "FastAPI server is not running"
    fi

    if curl -s --connect-timeout 5 "http://localhost:5001/status" >/dev/null 2>&1; then
        ((services_running++))
        print_success "Flask bridge is running"
    else
        print_warning "Flask bridge is not running"
    fi

    if [ $services_running -eq 0 ]; then
        print_warning "No services are running, skipping E2E tests"
        TEST_RESULTS["e2e"]="skipped"
        return 0
    fi

    # Run E2E tests
    cd "$ROBLOX_ENV"

    # Run individual E2E test files
    for test_file in "${e2e_test_files[@]}"; do
        if [ -f "$test_file" ]; then
            print_status "Running E2E test: $(basename "$test_file")"
            if pytest "${test_args[@]}" "$test_file"; then
                print_success "E2E test passed: $(basename "$test_file")"
            else
                print_error "E2E test failed: $(basename "$test_file")"
                TEST_RESULTS["e2e"]="failed"
                return 1
            fi
        fi
    done

    # Run E2E test directory if it exists
    if [ -d "$e2e_test_dir" ]; then
        print_status "Running E2E tests from $e2e_test_dir..."
        if pytest "${test_args[@]}" "$e2e_test_dir"; then
            print_success "E2E directory tests passed"
        else
            print_error "E2E directory tests failed"
            TEST_RESULTS["e2e"]="failed"
            return 1
        fi
    fi

    TEST_RESULTS["e2e"]="passed"
    print_success "All E2E tests passed"
    return 0
}

# Function to run performance tests
run_performance_tests() {
    print_header "RUNNING PERFORMANCE TESTS"

    local performance_test_dir="$ROBLOX_ENV/tests/performance"
    local test_args=()

    if [ "$VERBOSE" = true ]; then
        test_args+=("-v")
    fi

    if [ "$FAIL_FAST" = true ]; then
        test_args+=("-x")
    fi

    test_args+=("--html=$TEST_RESULTS_DIR/performance-test-report.html" "--self-contained-html")

    if [ -d "$performance_test_dir" ]; then
        print_status "Running performance tests from $performance_test_dir..."

        cd "$ROBLOX_ENV"
        if pytest "${test_args[@]}" "$performance_test_dir"; then
            TEST_RESULTS["performance"]="passed"
            print_success "Performance tests passed"
        else
            TEST_RESULTS["performance"]="failed"
            print_error "Performance tests failed"
            return 1
        fi
    else
        print_warning "Performance test directory not found, skipping performance tests"
        TEST_RESULTS["performance"]="skipped"
    fi

    return 0
}

# Function to run API tests
run_api_tests() {
    print_header "RUNNING API TESTS"

    local api_test_files=(
        "$ROBLOX_ENV/tests/test_fastapi_comprehensive.py"
        "$ROBLOX_ENV/tests/test_websocket_integration.py"
    )

    local test_args=()

    if [ "$VERBOSE" = true ]; then
        test_args+=("-v")
    fi

    if [ "$FAIL_FAST" = true ]; then
        test_args+=("-x")
    fi

    test_args+=("--html=$TEST_RESULTS_DIR/api-test-report.html" "--self-contained-html")

    cd "$ROBLOX_ENV"

    for test_file in "${api_test_files[@]}"; do
        if [ -f "$test_file" ]; then
            print_status "Running API test: $(basename "$test_file")"
            if pytest "${test_args[@]}" "$test_file"; then
                print_success "API test passed: $(basename "$test_file")"
            else
                print_error "API test failed: $(basename "$test_file")"
                TEST_RESULTS["api"]="failed"
                return 1
            fi
        fi
    done

    TEST_RESULTS["api"]="passed"
    print_success "All API tests passed"
    return 0
}

# Function to run workflow tests
run_workflow_tests() {
    print_header "RUNNING WORKFLOW TESTS"

    local workflow_test_file="$ROBLOX_ENV/tests/integration/test_workflows.py"
    local test_args=()

    if [ "$VERBOSE" = true ]; then
        test_args+=("-v")
    fi

    if [ "$FAIL_FAST" = true ]; then
        test_args+=("-x")
    fi

    test_args+=("--html=$TEST_RESULTS_DIR/workflow-test-report.html" "--self-contained-html")

    if [ -f "$workflow_test_file" ]; then
        print_status "Running workflow tests..."

        cd "$ROBLOX_ENV"
        if pytest "${test_args[@]}" "$workflow_test_file"; then
            TEST_RESULTS["workflow"]="passed"
            print_success "Workflow tests passed"
        else
            TEST_RESULTS["workflow"]="failed"
            print_error "Workflow tests failed"
            return 1
        fi
    else
        print_warning "Workflow test file not found, skipping workflow tests"
        TEST_RESULTS["workflow"]="skipped"
    fi

    return 0
}

# Function to run integration path verification
run_integration_verification() {
    print_header "RUNNING INTEGRATION PATH VERIFICATION"

    local verification_script="$SCRIPTS_DIR/integration/verify_integration_paths.sh"

    if [ -f "$verification_script" ]; then
        print_status "Running integration path verification..."

        if "$verification_script" --verbose; then
            TEST_RESULTS["integration_verification"]="passed"
            print_success "Integration path verification passed"
        else
            TEST_RESULTS["integration_verification"]="failed"
            print_error "Integration path verification failed"
            return 1
        fi
    else
        print_warning "Integration verification script not found, skipping"
        TEST_RESULTS["integration_verification"]="skipped"
    fi

    return 0
}

# Function to generate test report
generate_test_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        return 0
    fi

    print_header "GENERATING TEST REPORT"

    local report_file="$TEST_RESULTS_DIR/comprehensive-test-report.html"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>ToolboxAI Comprehensive Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 3px; }
        .passed { background-color: #d4edda; color: #155724; }
        .failed { background-color: #f8d7da; color: #721c24; }
        .skipped { background-color: #fff3cd; color: #856404; }
        .details { margin-top: 20px; }
        .coverage { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ToolboxAI Comprehensive Test Report</h1>
        <p>Generated: $timestamp</p>
        <p>Environment: $(uname -s) $(uname -r)</p>
    </div>

    <div class="summary">
        <h2>Test Summary</h2>
        <p><strong>Total Test Suites:</strong> ${#TEST_RESULTS[@]}</p>
        <p><strong>Passed:</strong> $(echo "${TEST_RESULTS[@]}" | tr ' ' '\n' | grep -c "passed" || echo "0")</p>
        <p><strong>Failed:</strong> $(echo "${TEST_RESULTS[@]}" | tr ' ' '\n' | grep -c "failed" || echo "0")</p>
        <p><strong>Skipped:</strong> $(echo "${TEST_RESULTS[@]}" | tr ' ' '\n' | grep -c "skipped" || echo "0")</p>
    </div>

    <div class="details">
        <h2>Test Results</h2>
EOF

    for test_type in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[$test_type]}"
        local class=""
        case "$result" in
            "passed") class="passed" ;;
            "failed") class="failed" ;;
            "skipped") class="skipped" ;;
        esac

        cat >> "$report_file" << EOF
        <div class="test-result $class">
            <strong>$test_type:</strong> $result
        </div>
EOF
    done

    cat >> "$report_file" << EOF
    </div>

    <div class="coverage">
        <h2>Coverage Reports</h2>
        <p><a href="coverage-unit/index.html">Unit Test Coverage</a></p>
        <p><a href="coverage-integration/index.html">Integration Test Coverage</a></p>
    </div>

    <div class="details">
        <h2>Individual Test Reports</h2>
        <p><a href="unit-test-report.html">Unit Test Report</a></p>
        <p><a href="integration-test-report.html">Integration Test Report</a></p>
        <p><a href="e2e-test-report.html">E2E Test Report</a></p>
        <p><a href="performance-test-report.html">Performance Test Report</a></p>
        <p><a href="api-test-report.html">API Test Report</a></p>
        <p><a href="workflow-test-report.html">Workflow Test Report</a></p>
    </div>
</body>
</html>
EOF

    print_success "Test report generated: $report_file"
}

# Function to show test summary
show_test_summary() {
    print_header "TEST SUMMARY"

    local total_suites=${#TEST_RESULTS[@]}
    local passed_suites=0
    local failed_suites=0
    local skipped_suites=0

    for result in "${TEST_RESULTS[@]}"; do
        case "$result" in
            "passed") ((passed_suites++)) ;;
            "failed") ((failed_suites++)) ;;
            "skipped") ((skipped_suites++)) ;;
        esac
    done

    echo -e "${BLUE}📊 Test Suite Results:${NC}"
    echo "  Total Suites: $total_suites"
    echo "  Passed: $passed_suites"
    echo "  Failed: $failed_suites"
    echo "  Skipped: $skipped_suites"
    echo ""

    echo -e "${BLUE}📋 Detailed Results:${NC}"
    for test_type in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[$test_type]}"
        local icon="✅"
        case "$result" in
            "failed") icon="❌" ;;
            "skipped") icon="⏭️" ;;
        esac
        echo "  $icon $test_type: $result"
    done

    echo ""
    if [ $failed_suites -eq 0 ]; then
        print_success "🎉 All test suites passed!"
        if [ "$GENERATE_REPORT" = true ]; then
            echo -e "${BLUE}📄 Test report available at: $TEST_RESULTS_DIR/comprehensive-test-report.html${NC}"
        fi
        return 0
    else
        print_error "⚠️  $failed_suites test suite(s) failed"
        return 1
    fi
}

# Main execution function
main() {
    print_header "TOOLBOXAI COMPREHENSIVE TESTING"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type=*)
                TEST_TYPE="${1#*=}"
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --coverage)
                COVERAGE=true
                shift
                ;;
            --parallel)
                PARALLEL=true
                shift
                ;;
            --fail-fast)
                FAIL_FAST=true
                shift
                ;;
            --no-report)
                GENERATE_REPORT=false
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --type=TYPE         Test type: all, unit, integration, e2e, performance, api, workflow"
                echo "  --verbose           Show verbose output"
                echo "  --coverage          Generate coverage reports"
                echo "  --parallel          Run tests in parallel"
                echo "  --fail-fast         Stop on first failure"
                echo "  --no-report         Skip report generation"
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

    # Check prerequisites
    check_prerequisites

    # Run tests based on type
    case "$TEST_TYPE" in
        "all")
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            run_performance_tests
            run_api_tests
            run_workflow_tests
            run_integration_verification
            ;;
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            run_integration_verification
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "api")
            run_api_tests
            ;;
        "workflow")
            run_workflow_tests
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            exit 1
            ;;
    esac

    # Generate report and show summary
    generate_test_report
    show_test_summary
}

# Run main function
main "$@"
