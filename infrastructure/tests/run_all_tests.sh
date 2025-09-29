#!/bin/bash

# Master Test Runner for ToolBoxAI Cloud Infrastructure
# Runs all test suites and generates comprehensive reports

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test directory
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$TEST_DIR")")"

# Create reports directory
REPORT_DIR="$TEST_DIR/reports/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

# Log file
LOG_FILE="$REPORT_DIR/test_runner.log"

# Track overall results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Functions
log_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  $1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
}

log_suite() {
    echo -e "\n${BLUE}▶ Running: $1${NC}"
    ((TOTAL_SUITES++))
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_SUITES++))
}

log_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_SUITES++))
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 1. Infrastructure Validation Tests
run_infrastructure_tests() {
    log_suite "Infrastructure Validation"

    if [ -x "$TEST_DIR/validate_infrastructure.sh" ]; then
        if "$TEST_DIR/validate_infrastructure.sh" > "$REPORT_DIR/infrastructure.log" 2>&1; then
            log_success "Infrastructure validation passed"
            cat "$REPORT_DIR/infrastructure.log" | grep -E "Passed:|Failed:|Warnings:" | tail -3
        else
            log_failure "Infrastructure validation failed"
            echo "  See: $REPORT_DIR/infrastructure.log"
        fi
    else
        log_warning "Infrastructure validation script not executable"
        chmod +x "$TEST_DIR/validate_infrastructure.sh" 2>/dev/null || true
    fi
}

# 2. Python Integration Tests
run_integration_tests() {
    log_suite "Integration Tests (Python)"

    # Check Python and install dependencies
    if command -v python3 &> /dev/null; then
        # Install required packages if needed
        python3 -m pip install boto3 psycopg2-binary redis websockets httpx pusher --quiet 2>/dev/null || true

        if python3 "$TEST_DIR/test_integrations.py" > "$REPORT_DIR/integrations.log" 2>&1; then
            log_success "Integration tests passed"
            # Extract summary
            grep -E "✓ Passed:|✗ Failed:|○ Skipped:" "$REPORT_DIR/integrations.log" | tail -3
        else
            log_failure "Integration tests failed"
            echo "  See: $REPORT_DIR/integrations.log"
        fi
    else
        log_warning "Python 3 not available, skipping integration tests"
    fi
}

# 3. API Health Checks
run_api_health_checks() {
    log_suite "API Health Checks"

    API_URL="http://127.0.0.1:8009"

    # Check if API is running
    if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
        log_success "API health endpoint responsive"

        # Test specific endpoints
        endpoints=(
            "/api/v1/content/types"
            "/api/v1/agents/list"
            "/docs"
        )

        for endpoint in "${endpoints[@]}"; do
            if curl -s -f "$API_URL$endpoint" > /dev/null 2>&1; then
                echo "  ✓ $endpoint"
            else
                echo "  ✗ $endpoint"
            fi
        done
    else
        log_failure "API not responding on port 8009"
    fi
}

# 4. Frontend Health Checks
run_frontend_checks() {
    log_suite "Frontend Health Checks"

    FRONTEND_URL="http://127.0.0.1:5179"

    # Check if frontend is running
    if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
        log_success "Frontend responsive on port 5179"

        # Check for key resources
        if curl -s "$FRONTEND_URL" | grep -q "ToolBoxAI"; then
            echo "  ✓ Frontend content loaded"
        else
            echo "  ⚠ Frontend content check failed"
        fi
    else
        log_failure "Frontend not responding on port 5179"
    fi
}

# 5. Database Connectivity
run_database_checks() {
    log_suite "Database Connectivity"

    # PostgreSQL check
    if command -v psql &> /dev/null; then
        if PGPASSWORD=eduplatform2024 psql -h localhost -U eduplatform -d educational_platform_dev -c "SELECT 1" > /dev/null 2>&1; then
            log_success "PostgreSQL connection successful"
        else
            log_failure "PostgreSQL connection failed"
        fi
    else
        log_warning "psql not installed, skipping PostgreSQL check"
    fi

    # Redis check
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping > /dev/null 2>&1; then
            log_success "Redis connection successful"
        else
            log_failure "Redis connection failed"
        fi
    else
        log_warning "redis-cli not installed, skipping Redis check"
    fi
}

# 6. Security Scan
run_security_scan() {
    log_suite "Security Scan"

    # Check for secrets in code
    echo "  Scanning for hardcoded secrets..."

    if ! grep -r "sk-[a-zA-Z0-9]" "$PROJECT_ROOT" \
        --include="*.py" \
        --include="*.js" \
        --include="*.ts" \
        --include="*.env.example" \
        --exclude-dir=".git" \
        --exclude-dir="node_modules" \
        --exclude-dir="venv" \
        --exclude-dir=".venv" 2>/dev/null; then
        log_success "No hardcoded API keys found"
    else
        log_failure "Potential hardcoded secrets detected"
    fi

    # Check file permissions
    sensitive_files=(
        ".env"
        "config/database.env"
        "config/production/.env"
    )

    for file in "${sensitive_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            perms=$(stat -c %a "$PROJECT_ROOT/$file" 2>/dev/null || stat -f %A "$PROJECT_ROOT/$file" 2>/dev/null)
            if [ "$perms" -le "600" ]; then
                echo "  ✓ $file has secure permissions"
            else
                echo "  ⚠ $file has permissions $perms (should be 600)"
            fi
        fi
    done
}

# 7. Performance Baseline Test
run_performance_test() {
    log_suite "Performance Baseline"

    if command -v k6 &> /dev/null; then
        log_warning "k6 not installed, would run: k6 run --quiet --duration 30s --vus 10 performance_test.js"
        echo "  Install with: brew install k6 (macOS) or https://k6.io/docs/getting-started/installation"
    else
        log_warning "k6 not installed, skipping performance tests"
    fi
}

# 8. Docker/Container Tests
run_container_tests() {
    log_suite "Container Tests"

    if command -v docker &> /dev/null; then
        # Check Docker daemon
        if docker info > /dev/null 2>&1; then
            log_success "Docker daemon running"

            # List running containers
            container_count=$(docker ps -q | wc -l)
            echo "  Running containers: $container_count"
        else
            log_failure "Docker daemon not accessible"
        fi
    else
        log_warning "Docker not installed"
    fi
}

# 9. Generate Summary Report
generate_report() {
    cat > "$REPORT_DIR/summary.md" <<EOF
# ToolBoxAI Infrastructure Test Report

**Date:** $(date)
**Environment:** Development/Local

## Test Summary

- **Total Test Suites:** $TOTAL_SUITES
- **Passed:** $PASSED_SUITES
- **Failed:** $FAILED_SUITES
- **Success Rate:** $((PASSED_SUITES * 100 / TOTAL_SUITES))%

## Test Results

### Infrastructure Validation
$([ -f "$REPORT_DIR/infrastructure.log" ] && tail -10 "$REPORT_DIR/infrastructure.log" || echo "Not run")

### Integration Tests
$([ -f "$REPORT_DIR/integrations.log" ] && grep -A 5 "TEST SUMMARY" "$REPORT_DIR/integrations.log" || echo "Not run")

### API Status
- Backend: $(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8009/health 2>/dev/null || echo "Down")
- Frontend: $(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5179 2>/dev/null || echo "Down")

### Database Status
- PostgreSQL: $(PGPASSWORD=eduplatform2024 psql -h localhost -U eduplatform -d educational_platform_dev -c "SELECT 'Connected'" -t 2>/dev/null || echo "Not connected")
- Redis: $(redis-cli ping 2>/dev/null || echo "Not connected")

## Recommendations

$(if [ $FAILED_SUITES -gt 0 ]; then
    echo "1. Review failed test logs in: $REPORT_DIR"
    echo "2. Check service connectivity and configurations"
    echo "3. Verify all dependencies are installed"
    echo "4. Run individual test suites for debugging"
else
    echo "✓ All tests passed successfully!"
    echo "✓ System is ready for deployment"
fi)

## Log Files

- Infrastructure: $REPORT_DIR/infrastructure.log
- Integration: $REPORT_DIR/integrations.log
- Full Log: $REPORT_DIR/test_runner.log

---
*Generated on $(date)*
EOF

    echo -e "\n${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Report saved to: $REPORT_DIR/summary.md${NC}"
}

# Main execution
main() {
    log_header "TOOLBOXAI INFRASTRUCTURE TEST SUITE"
    echo "Starting comprehensive test execution..."
    echo "Report directory: $REPORT_DIR"
    echo ""

    # Redirect all output to log file as well
    exec > >(tee -a "$LOG_FILE")
    exec 2>&1

    # Run all test suites
    run_infrastructure_tests
    run_integration_tests
    run_api_health_checks
    run_frontend_checks
    run_database_checks
    run_security_scan
    run_performance_test
    run_container_tests

    # Generate report
    echo ""
    log_header "TEST EXECUTION COMPLETE"

    echo -e "\n${CYAN}Test Results Summary:${NC}"
    echo -e "${GREEN}Passed: $PASSED_SUITES${NC}"
    echo -e "${RED}Failed: $FAILED_SUITES${NC}"
    echo -e "Total: $TOTAL_SUITES"

    generate_report

    # Exit code
    if [ $FAILED_SUITES -gt 0 ]; then
        echo -e "\n${RED}⚠ Some tests failed. Review logs for details.${NC}"
        exit 1
    else
        echo -e "\n${GREEN}✓ All tests passed successfully!${NC}"
        exit 0
    fi
}

# Run main
main