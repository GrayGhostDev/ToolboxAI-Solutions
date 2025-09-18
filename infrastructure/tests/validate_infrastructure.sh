#!/bin/bash

# Infrastructure Validation Test Suite
# Tests all infrastructure components for ToolBoxAI Solutions

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNINGS++))
}

# Test Terraform Configuration
test_terraform() {
    log_info "Testing Terraform Configuration..."

    cd ../terraform

    # Check Terraform syntax
    if terraform fmt -check=true -diff > /dev/null 2>&1; then
        log_success "Terraform formatting is correct"
    else
        log_error "Terraform formatting issues found"
        terraform fmt -diff
    fi

    # Validate Terraform configuration
    if terraform init -backend=false > /dev/null 2>&1; then
        if terraform validate > /dev/null 2>&1; then
            log_success "Terraform configuration is valid"
        else
            log_error "Terraform validation failed"
            terraform validate
        fi
    else
        log_error "Terraform initialization failed"
    fi

    # Check for required variables
    if grep -q "variable \"environment\"" variables.tf; then
        log_success "Required environment variable defined"
    else
        log_error "Missing environment variable definition"
    fi

    # Check for remote state configuration
    if grep -q "backend \"s3\"" main.tf; then
        log_success "Remote state backend configured"
    else
        log_warning "Remote state backend not configured"
    fi

    cd ../tests
}

# Test Kubernetes Manifests
test_kubernetes() {
    log_info "Testing Kubernetes Manifests..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_warning "kubectl not installed, skipping Kubernetes tests"
        return
    fi

    # Validate YAML syntax
    for file in ../kubernetes/apps/**/*.yaml; do
        if [ -f "$file" ]; then
            if kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
                log_success "Valid manifest: $(basename $file)"
            else
                log_error "Invalid manifest: $(basename $file)"
                kubectl apply --dry-run=client -f "$file"
            fi
        fi
    done

    # Check for required resources
    if [ -f "../kubernetes/apps/backend/deployment.yaml" ]; then
        log_success "Backend deployment manifest exists"
    else
        log_error "Backend deployment manifest missing"
    fi

    if [ -f "../kubernetes/apps/mcp/servers/deployment.yaml" ]; then
        log_success "MCP server deployment manifest exists"
    else
        log_error "MCP server deployment manifest missing"
    fi
}

# Test Docker Configurations
test_docker() {
    log_info "Testing Docker Configurations..."

    # Check Dockerfile syntax
    for dockerfile in ../docker/*.Dockerfile; do
        if [ -f "$dockerfile" ]; then
            if docker build -f "$dockerfile" --no-cache -t test-image:latest . > /dev/null 2>&1; then
                log_success "Valid Dockerfile: $(basename $dockerfile)"
                docker rmi test-image:latest > /dev/null 2>&1
            else
                log_error "Invalid Dockerfile: $(basename $dockerfile)"
            fi
        fi
    done

    # Check for security best practices
    for dockerfile in ../docker/*.Dockerfile; do
        if [ -f "$dockerfile" ]; then
            # Check for non-root user
            if grep -q "USER" "$dockerfile"; then
                log_success "Non-root user configured in $(basename $dockerfile)"
            else
                log_warning "No USER directive in $(basename $dockerfile)"
            fi

            # Check for health checks
            if grep -q "HEALTHCHECK" "$dockerfile"; then
                log_success "Health check configured in $(basename $dockerfile)"
            else
                log_warning "No HEALTHCHECK in $(basename $dockerfile)"
            fi
        fi
    done
}

# Test CI/CD Configuration
test_cicd() {
    log_info "Testing CI/CD Configuration..."

    # Check GitHub Actions workflow
    workflow_file="../../.github/workflows/deploy.yml"
    if [ -f "$workflow_file" ]; then
        log_success "GitHub Actions workflow exists"

        # Check for required jobs
        if grep -q "name: Test" "$workflow_file"; then
            log_success "Test job configured"
        else
            log_warning "No test job in workflow"
        fi

        if grep -q "name: Deploy" "$workflow_file"; then
            log_success "Deploy job configured"
        else
            log_error "No deploy job in workflow"
        fi
    else
        log_error "GitHub Actions workflow missing"
    fi
}

# Test Monitoring Configuration
test_monitoring() {
    log_info "Testing Monitoring Configuration..."

    # Check Prometheus configuration
    if [ -f "../monitoring/prometheus/values.yaml" ]; then
        log_success "Prometheus configuration exists"

        # Check for MCP metrics configuration
        if grep -q "mcp-server" "../monitoring/prometheus/values.yaml"; then
            log_success "MCP server metrics configured"
        else
            log_warning "MCP server metrics not configured"
        fi
    else
        log_error "Prometheus configuration missing"
    fi

    # Check Grafana dashboards
    if [ -d "../monitoring/grafana/dashboards" ]; then
        dashboard_count=$(ls -1 ../monitoring/grafana/dashboards/*.json 2>/dev/null | wc -l)
        if [ "$dashboard_count" -gt 0 ]; then
            log_success "Found $dashboard_count Grafana dashboards"
        else
            log_warning "No Grafana dashboards found"
        fi
    else
        log_warning "Grafana dashboards directory missing"
    fi
}

# Test Security Configuration
test_security() {
    log_info "Testing Security Configuration..."

    # Check for secrets in code
    log_info "Scanning for hardcoded secrets..."
    if ! grep -r "sk-[a-zA-Z0-9]" ../ --include="*.tf" --include="*.yaml" --include="*.yml" 2>/dev/null; then
        log_success "No hardcoded API keys found"
    else
        log_error "Potential hardcoded secrets detected"
    fi

    # Check IAM policies
    if [ -f "../terraform/modules/iam/policies.json" ]; then
        log_success "IAM policies defined"
    else
        log_warning "IAM policies file not found"
    fi

    # Check network security
    if grep -q "ingress_rules" ../terraform/modules/security/*.tf 2>/dev/null; then
        log_success "Network security rules configured"
    else
        log_warning "Network security rules not found"
    fi
}

# Test MCP Configuration
test_mcp() {
    log_info "Testing MCP Configuration..."

    # Check MCP server configuration
    if [ -f "../mcp/servers/config.json" ]; then
        log_success "MCP server configuration exists"

        # Validate JSON syntax
        if python3 -m json.tool ../mcp/servers/config.json > /dev/null 2>&1; then
            log_success "Valid MCP server configuration JSON"
        else
            log_error "Invalid MCP server configuration JSON"
        fi
    else
        log_error "MCP server configuration missing"
    fi

    # Check agent configurations
    agent_count=$(ls -1 ../mcp/agents/*.yaml 2>/dev/null | wc -l)
    if [ "$agent_count" -gt 0 ]; then
        log_success "Found $agent_count agent configurations"
    else
        log_error "No agent configurations found"
    fi
}

# Main test execution
main() {
    echo "========================================"
    echo "Infrastructure Validation Test Suite"
    echo "========================================"
    echo ""

    test_terraform
    echo ""

    test_kubernetes
    echo ""

    test_docker
    echo ""

    test_cicd
    echo ""

    test_monitoring
    echo ""

    test_security
    echo ""

    test_mcp
    echo ""

    # Print summary
    echo "========================================"
    echo "Test Summary"
    echo "========================================"
    echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
    echo -e "${RED}Failed:${NC} $FAILED_TESTS"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
    echo -e "Total Tests: $TOTAL_TESTS"

    # Exit with appropriate code
    if [ "$FAILED_TESTS" -gt 0 ]; then
        echo -e "\n${RED}Infrastructure validation failed!${NC}"
        exit 1
    else
        echo -e "\n${GREEN}Infrastructure validation passed!${NC}"
        exit 0
    fi
}

# Run tests
main "$@"