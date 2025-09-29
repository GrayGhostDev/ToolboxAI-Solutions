#!/bin/bash
# ============================================
# INFRASTRUCTURE SECURITY SCANNER
# ============================================
# Scans for hardcoded secrets, passwords, and security issues
# ============================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCAN_DIR="${1:-.}"
VIOLATIONS=0

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}TOOLBOXAI INFRASTRUCTURE SECURITY SCAN${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "${YELLOW}Scanning directory: ${SCAN_DIR}${NC}"

# Function to report violation
report_violation() {
    local file="$1"
    local line="$2"
    local pattern="$3"
    local content="$4"
    
    ((VIOLATIONS++))
    echo -e "${RED}❌ SECURITY VIOLATION ${VIOLATIONS}${NC}"
    echo -e "${YELLOW}File: ${file}:${line}${NC}"
    echo -e "${YELLOW}Pattern: ${pattern}${NC}"
    echo -e "${RED}Content: ${content}${NC}"
    echo ""
}

# Function to scan for patterns
scan_pattern() {
    local pattern="$1"
    local description="$2"
    local exclude_pattern="${3:-}"
    
    echo -e "${BLUE}Scanning for: ${description}${NC}"
    
    local results
    if [[ -n "$exclude_pattern" ]]; then
        results=$(grep -rn --include="*.yml" --include="*.yaml" --include="*.sh" --include="*.py" --include="*.js" --include="*.json" --include="*.tf" -E "$pattern" "$SCAN_DIR" | grep -v -E "$exclude_pattern" || true)
    else
        results=$(grep -rn --include="*.yml" --include="*.yaml" --include="*.sh" --include="*.py" --include="*.js" --include="*.json" --include="*.tf" -E "$pattern" "$SCAN_DIR" || true)
    fi
    
    if [[ -n "$results" ]]; then
        while IFS= read -r line; do
            local file=$(echo "$line" | cut -d: -f1)
            local line_num=$(echo "$line" | cut -d: -f2)
            local content=$(echo "$line" | cut -d: -f3-)
            report_violation "$file" "$line_num" "$pattern" "$content"
        done <<< "$results"
    else
        echo -e "${GREEN}✅ No violations found${NC}"
    fi
    echo ""
}

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}RUNNING SECURITY SCANS${NC}"
echo -e "${BLUE}============================================${NC}"

# Scan for hardcoded passwords
scan_pattern "password\s*[:=]\s*[\"'][^\"']{8,}[\"']" "Hardcoded passwords" "(devpass|testpass|change-me|USE_KUBECTL|your-|admin.*admin|\\\${.*})"

# Scan for API keys
scan_pattern "sk-[a-zA-Z0-9]{40,}" "OpenAI API keys"

# Scan for JWT secrets
scan_pattern "jwt[_-]?secret\s*[:=]\s*[\"'][^\"']{20,}[\"']" "Hardcoded JWT secrets" "(change-me|dev-secret|USE_KUBECTL|\\\${.*})"

# Scan for database connection strings with passwords
scan_pattern "postgresql://[^:]+:[^@/]+@" "Database URLs with passwords" "(\\\${.*}|your-|test)"

# Scan for Redis AUTH passwords
scan_pattern "AUTH\s+[a-zA-Z0-9]{10,}" "Redis AUTH passwords"

# Scan for private keys
scan_pattern "-----BEGIN.*PRIVATE KEY-----" "Private key files"

# Scan for access tokens
scan_pattern "(access_token|token)\s*[:=]\s*[\"'][a-zA-Z0-9]{20,}[\"']" "Access tokens" "(\\\${.*}|your-|test|example)"

# Scan for credentials in file names
echo -e "${BLUE}Scanning for credential files${NC}"
cred_files=$(find "$SCAN_DIR" -type f \( -name "*secret*" -o -name "*password*" -o -name "*key*" -o -name "*.pem" -o -name "*.p12" -o -name "*.pfx" \) | grep -v -E "(example|template|\.md$|\.gitignore$|security-scan\.sh|configmap|\.sh$)" || true)

if [[ -n "$cred_files" ]]; then
    while IFS= read -r file; do
        if [[ -f "$file" && -s "$file" ]]; then
            report_violation "$file" "N/A" "Credential file" "File contains potential credentials"
        fi
    done <<< "$cred_files"
else
    echo -e "${GREEN}✅ No credential files found${NC}"
fi
echo ""

# Check .gitignore coverage
echo -e "${BLUE}Checking .gitignore coverage${NC}"
gitignore_file="$SCAN_DIR/../.gitignore"
if [[ -f "$gitignore_file" ]]; then
    required_patterns=("*secret*" "*.key" "*.pem" "infrastructure/docker/secrets/" "*.tfvars")
    missing_patterns=()
    
    for pattern in "${required_patterns[@]}"; do
        if ! grep -q "$pattern" "$gitignore_file"; then
            missing_patterns+=("$pattern")
        fi
    done
    
    if [[ ${#missing_patterns[@]} -gt 0 ]]; then
        report_violation "$gitignore_file" "N/A" "Missing .gitignore patterns" "${missing_patterns[*]}"
    else
        echo -e "${GREEN}✅ .gitignore has proper security patterns${NC}"
    fi
else
    report_violation "." "N/A" "Missing .gitignore" "No .gitignore file found"
fi
echo ""

# Check for Docker secrets properly configured
echo -e "${BLUE}Checking Docker Compose security${NC}"
compose_files=$(find "$SCAN_DIR" -name "docker-compose*.yml" -o -name "compose*.yml")
if [[ -n "$compose_files" ]]; then
    while IFS= read -r file; do
        if grep -q "POSTGRES_PASSWORD.*:" "$file" && ! grep -q "_FILE:" "$file" && ! grep -q "\${" "$file"; then
            report_violation "$file" "N/A" "Insecure password handling" "Uses direct password instead of secrets or env vars"
        fi
    done <<< "$compose_files"
    echo -e "${GREEN}✅ Docker Compose files checked${NC}"
else
    echo -e "${YELLOW}⚠️  No Docker Compose files found${NC}"
fi
echo ""

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}SECURITY SCAN SUMMARY${NC}"
echo -e "${BLUE}============================================${NC}"

if [[ $VIOLATIONS -eq 0 ]]; then
    echo -e "${GREEN}🎉 SECURITY SCAN PASSED!${NC}"
    echo -e "${GREEN}No security violations found${NC}"
    exit 0
else
    echo -e "${RED}🚨 SECURITY SCAN FAILED!${NC}"
    echo -e "${RED}Found ${VIOLATIONS} security violation(s)${NC}"
    echo ""
    echo -e "${YELLOW}REMEDIATION STEPS:${NC}"
    echo -e "${YELLOW}1. Remove all hardcoded secrets${NC}"
    echo -e "${YELLOW}2. Use environment variables or secret management${NC}"
    echo -e "${YELLOW}3. Update .gitignore to exclude credential files${NC}"
    echo -e "${YELLOW}4. Rotate any exposed credentials${NC}"
    echo -e "${YELLOW}5. Review access logs for unauthorized usage${NC}"
    exit 1
fi
