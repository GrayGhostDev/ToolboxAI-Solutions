#!/bin/bash
# ToolboxAI Solutions - Security Audit Script
# Runs comprehensive security checks on all dependencies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPORT_DIR="./security_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/security_audit_${TIMESTAMP}.md"

echo -e "${BLUE}🔒 ToolboxAI Solutions - Security Audit${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Activate venv_clean environment for Python security tools
if [ -f "ToolboxAI-Roblox-Environment/venv_clean/bin/activate" ]; then
    echo -e "${YELLOW}🐍 Activating venv_clean environment...${NC}"
    source ToolboxAI-Roblox-Environment/venv_clean/bin/activate
    echo -e "${GREEN}✅ venv_clean activated: $(which python)${NC}"
else
    echo -e "${RED}⚠️  venv_clean not found at ToolboxAI-Roblox-Environment/venv_clean/${NC}"
    echo -e "${YELLOW}   Continuing with system Python...${NC}"
fi
echo ""

# Create reports directory
mkdir -p "$REPORT_DIR"

# Initialize report
cat > "$REPORT_FILE" << 'EOF'
# 🛡️ Security Audit Report - PLACEHOLDER_DATE

## 📋 Executive Summary

**Audit Date**: PLACEHOLDER_DATE  
**Audit Type**: Automated Dependency Security Scan  
**Python Environment**: venv_clean (ToolboxAI-Roblox-Environment/venv_clean)  
**Scope**: All Python and Node.js dependencies  

---

## 🐍 Python Security Audit

EOF

# Replace placeholders with actual date
sed -i "s/PLACEHOLDER_DATE/$(date)/g" "$REPORT_FILE"

echo -e "${BLUE}🔍 Starting Python Security Audit...${NC}"

# Function to audit Python requirements
audit_python_requirements() {
    local req_file=$1
    local project_name=$(basename "$(dirname "$req_file")")
    
    echo -e "${YELLOW}  📦 Checking: $req_file${NC}"
    
    if [ ! -f "$req_file" ]; then
        echo -e "${RED}    ❌ File not found: $req_file${NC}"
        return 1
    fi
    
    # Add to report
    echo "### $project_name" >> "$REPORT_FILE"
    echo "**File**: \`$req_file\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Check if pip-audit is available
    if command -v pip-audit &> /dev/null; then
        echo -e "${BLUE}    🔍 Running pip-audit...${NC}"
        
        # Run pip-audit and capture output
        if pip-audit --requirement "$req_file" --format json --output "${REPORT_DIR}/pip-audit-${project_name}-${TIMESTAMP}.json" 2>/dev/null; then
            echo -e "${GREEN}    ✅ No vulnerabilities found${NC}"
            echo "✅ **Status**: No vulnerabilities detected" >> "$REPORT_FILE"
        else
            echo -e "${YELLOW}    ⚠️  Vulnerabilities found - check report${NC}"
            echo "⚠️ **Status**: Vulnerabilities detected - see detailed report" >> "$REPORT_FILE"
        fi
    else
        echo -e "${YELLOW}    ⚠️  pip-audit not installed, installing...${NC}"
        pip install pip-audit
        pip-audit --requirement "$req_file" --format json --output "${REPORT_DIR}/pip-audit-${project_name}-${TIMESTAMP}.json" 2>/dev/null || true
    fi
    
    # Check if safety is available
    if command -v safety &> /dev/null; then
        echo -e "${BLUE}    🔍 Running safety check...${NC}"
        
        # Run safety check
        if safety check --file "$req_file" --json --output "${REPORT_DIR}/safety-${project_name}-${TIMESTAMP}.json" 2>/dev/null; then
            echo -e "${GREEN}    ✅ Safety check passed${NC}"
        else
            echo -e "${YELLOW}    ⚠️  Safety issues found${NC}"
        fi
    else
        echo -e "${YELLOW}    ⚠️  safety not installed, installing...${NC}"
        pip install safety
        safety check --file "$req_file" --json --output "${REPORT_DIR}/safety-${project_name}-${TIMESTAMP}.json" 2>/dev/null || true
    fi
    
    echo "" >> "$REPORT_FILE"
}

# Find and audit all requirements files
echo -e "${BLUE}📁 Finding Python requirements files...${NC}"

find . -name "requirements*.txt" -not -path "./venv*" -not -path "./.venv*" -not -path "./node_modules/*" | while read req_file; do
    audit_python_requirements "$req_file"
done

# Add Node.js section to report
cat >> "$REPORT_FILE" << EOF

---

## 🟢 Node.js Security Audit

EOF

echo -e "${BLUE}🔍 Starting Node.js Security Audit...${NC}"

# Function to audit Node.js packages
audit_nodejs_packages() {
    local package_file=$1
    local project_name=$(basename "$(dirname "$package_file")")
    
    echo -e "${YELLOW}  📦 Checking: $package_file${NC}"
    
    if [ ! -f "$package_file" ]; then
        echo -e "${RED}    ❌ File not found: $package_file${NC}"
        return 1
    fi
    
    # Change to the directory containing package.json
    pushd "$(dirname "$package_file")" > /dev/null
    
    # Add to report
    echo "### $project_name" >> "$REPORT_FILE"
    echo "**File**: \`$package_file\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Run npm audit
    if command -v npm &> /dev/null; then
        echo -e "${BLUE}    🔍 Running npm audit...${NC}"
        
        # Run npm audit
        if npm audit --json > "${REPORT_DIR}/npm-audit-${project_name}-${TIMESTAMP}.json" 2>/dev/null; then
            echo -e "${GREEN}    ✅ No vulnerabilities found${NC}"
            echo "✅ **Status**: No vulnerabilities detected" >> "$REPORT_FILE"
        else
            # Get audit results
            audit_result=$(npm audit --json 2>/dev/null || echo '{"metadata":{"vulnerabilities":{"total":0}}}')
            vuln_count=$(echo "$audit_result" | jq -r '.metadata.vulnerabilities.total' 2>/dev/null || echo "unknown")
            
            if [ "$vuln_count" = "0" ]; then
                echo -e "${GREEN}    ✅ No vulnerabilities found${NC}"
                echo "✅ **Status**: No vulnerabilities detected" >> "$REPORT_FILE"
            else
                echo -e "${YELLOW}    ⚠️  $vuln_count vulnerabilities found${NC}"
                echo "⚠️ **Status**: $vuln_count vulnerabilities detected" >> "$REPORT_FILE"
            fi
        fi
    else
        echo -e "${RED}    ❌ npm not available${NC}"
        echo "❌ **Status**: npm not available for audit" >> "$REPORT_FILE"
    fi
    
    # Check for yarn if available
    if command -v yarn &> /dev/null && [ -f "yarn.lock" ]; then
        echo -e "${BLUE}    🔍 Running yarn audit...${NC}"
        
        if yarn audit --json > "${REPORT_DIR}/yarn-audit-${project_name}-${TIMESTAMP}.json" 2>/dev/null; then
            echo -e "${GREEN}    ✅ Yarn audit passed${NC}"
        else
            echo -e "${YELLOW}    ⚠️  Yarn audit found issues${NC}"
        fi
    fi
    
    popd > /dev/null
    echo "" >> "$REPORT_FILE"
}

# Find and audit all package.json files
echo -e "${BLUE}📁 Finding Node.js package files...${NC}"

find . -name "package.json" -not -path "./node_modules/*" | while read package_file; do
    audit_nodejs_packages "$package_file"
done

# Add summary to report
cat >> "$REPORT_FILE" << EOF

---

## 📊 Audit Summary

**Completed**: $(date)  
**Duration**: Automated scan  
**Files Audited**: 
- Python requirements files: $(find . -name "requirements*.txt" -not -path "./venv*" -not -path "./.venv*" -not -path "./node_modules/*" | wc -l)
- Node.js package files: $(find . -name "package.json" -not -path "./node_modules/*" | wc -l)

### 📁 Detailed Reports

Individual audit reports saved to:
- **Directory**: \`$REPORT_DIR\`
- **pip-audit reports**: \`pip-audit-*-${TIMESTAMP}.json\`
- **safety reports**: \`safety-*-${TIMESTAMP}.json\`  
- **npm audit reports**: \`npm-audit-*-${TIMESTAMP}.json\`

### 🔧 Recommended Actions

1. **High/Critical Vulnerabilities**: Update immediately
2. **Medium Vulnerabilities**: Plan updates within 1 week
3. **Low Vulnerabilities**: Include in next maintenance cycle
4. **False Positives**: Document and suppress if necessary

### 📞 Support

For questions about this security audit:
- **Email**: security@toolboxai.example.com
- **Documentation**: See \`SECURITY_REMEDIATION_REPORT.md\`
- **Emergency**: Follow incident response procedures

---

*Generated by ToolboxAI Security Audit Script v1.0*
EOF

echo ""
echo -e "${GREEN}✅ Security Audit Complete!${NC}"
echo -e "${BLUE}📄 Report saved to: $REPORT_FILE${NC}"
echo -e "${BLUE}📁 Detailed reports in: $REPORT_DIR${NC}"
echo ""

# Show summary of findings
echo -e "${BLUE}📊 Quick Summary:${NC}"

# Count Python requirements files
python_files=$(find . -name "requirements*.txt" -not -path "./venv*" -not -path "./.venv*" -not -path "./node_modules/*" | wc -l)
echo -e "${YELLOW}  🐍 Python requirements files scanned: $python_files${NC}"

# Count Node.js package files  
nodejs_files=$(find . -name "package.json" -not -path "./node_modules/*" | wc -l)
echo -e "${YELLOW}  🟢 Node.js package files scanned: $nodejs_files${NC}"

# Check if any JSON reports were created (indicates potential issues)
json_reports=$(ls "${REPORT_DIR}"/*-${TIMESTAMP}.json 2>/dev/null | wc -l)
if [ "$json_reports" -gt 0 ]; then
    echo -e "${YELLOW}  📋 Detailed reports created: $json_reports${NC}"
    echo -e "${YELLOW}  👉 Review individual JSON files for specific vulnerabilities${NC}"
else
    echo -e "${GREEN}  ✅ No detailed reports created (likely no issues found)${NC}"
fi

echo ""
echo -e "${BLUE}🔄 Next Steps:${NC}"
echo -e "${YELLOW}  1. Review the audit report: $REPORT_FILE${NC}"
echo -e "${YELLOW}  2. Address any high/critical vulnerabilities immediately${NC}"
echo -e "${YELLOW}  3. Plan updates for medium-priority issues${NC}"
echo -e "${YELLOW}  4. Schedule regular security audits (weekly recommended)${NC}"
echo ""

# Return appropriate exit code
if [ "$json_reports" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Potential security issues found - review reports${NC}"
    exit 1
else
    echo -e "${GREEN}✅ No obvious security issues detected${NC}"
    exit 0
fi