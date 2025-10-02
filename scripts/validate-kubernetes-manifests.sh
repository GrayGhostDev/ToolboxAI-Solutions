#!/bin/bash
# Kubernetes Manifest Validation Script
# Validates all Kubernetes manifests for syntax and best practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Kubernetes Manifest Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to validate YAML syntax
validate_yaml_syntax() {
    local file=$1
    if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to validate with kubectl (if available)
validate_kubectl() {
    local file=$1
    if command -v kubectl &> /dev/null; then
        if kubectl apply --dry-run=client -f "$file" &>/dev/null; then
            return 0
        else
            return 1
        fi
    else
        # kubectl not available, skip
        return 2
    fi
}

# Function to check for common issues
check_best_practices() {
    local file=$1
    local issues=()

    # Check for resource limits
    if ! grep -q "limits:" "$file" 2>/dev/null; then
        if grep -q "kind: Deployment" "$file" || grep -q "kind: StatefulSet" "$file"; then
            issues+=("No resource limits defined")
        fi
    fi

    # Check for health checks
    if ! grep -q "livenessProbe:" "$file" 2>/dev/null; then
        if grep -q "kind: Deployment" "$file" || grep -q "kind: StatefulSet" "$file"; then
            issues+=("No liveness probe defined")
        fi
    fi

    # Check for readiness checks
    if ! grep -q "readinessProbe:" "$file" 2>/dev/null; then
        if grep -q "kind: Deployment" "$file" || grep -q "kind: StatefulSet" "$file"; then
            issues+=("No readiness probe defined")
        fi
    fi

    # Check for image pull policy
    if grep -q "image:" "$file" 2>/dev/null; then
        if ! grep -q "imagePullPolicy:" "$file" 2>/dev/null; then
            issues+=("No imagePullPolicy specified")
        fi
    fi

    # Check for security context
    if ! grep -q "securityContext:" "$file" 2>/dev/null; then
        if grep -q "kind: Deployment" "$file" || grep -q "kind: StatefulSet" "$file"; then
            issues+=("No securityContext defined")
        fi
    fi

    # Return issues
    if [ ${#issues[@]} -gt 0 ]; then
        echo "${issues[@]}"
        return 1
    else
        return 0
    fi
}

echo "Finding Kubernetes manifest files..."
echo ""

# Find all YAML files in kubernetes directory
K8S_DIR="infrastructure/kubernetes"

if [ ! -d "$K8S_DIR" ]; then
    echo -e "${RED}Error: Kubernetes directory not found: $K8S_DIR${NC}"
    exit 1
fi

# Process all YAML files
while IFS= read -r -d '' file; do
    TOTAL=$((TOTAL + 1))

    filename=$(basename "$file")
    dirname=$(dirname "$file" | sed "s|$K8S_DIR/||")

    echo -e "${BLUE}[$TOTAL] Validating: ${dirname}/${filename}${NC}"

    # Validate YAML syntax
    if validate_yaml_syntax "$file"; then
        echo -e "  ${GREEN}✓${NC} YAML syntax valid"
    else
        echo -e "  ${RED}✗${NC} YAML syntax invalid"
        FAILED=$((FAILED + 1))
        echo ""
        continue
    fi

    # Validate with kubectl (if available)
    kubectl_result=$(validate_kubectl "$file"; echo $?)
    if [ $kubectl_result -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} kubectl validation passed"
    elif [ $kubectl_result -eq 1 ]; then
        echo -e "  ${RED}✗${NC} kubectl validation failed"
        FAILED=$((FAILED + 1))
        echo ""
        continue
    else
        echo -e "  ${YELLOW}⊘${NC} kubectl not available (skipping)"
    fi

    # Check best practices
    if best_practice_issues=$(check_best_practices "$file"); then
        echo -e "  ${GREEN}✓${NC} Best practices validated"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${YELLOW}⚠${NC} Best practice warnings:"
        for issue in $best_practice_issues; do
            echo -e "    - ${issue}"
        done
        WARNINGS=$((WARNINGS + 1))
        PASSED=$((PASSED + 1))  # Still count as passed
    fi

    echo ""

done < <(find "$K8S_DIR" -type f \( -name "*.yaml" -o -name "*.yml" \) -print0)

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total files: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo -e "${YELLOW}Warnings: ${WARNINGS}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some validations failed${NC}"
    exit 1
fi
