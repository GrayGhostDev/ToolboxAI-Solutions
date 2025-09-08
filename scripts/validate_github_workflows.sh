#!/bin/bash
# Validate GitHub Actions workflows for syntax errors

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 GitHub Actions Workflow Validation${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d ".github/workflows" ]; then
    echo -e "${RED}❌ .github/workflows directory not found${NC}"
    echo -e "${YELLOW}   Please run this script from the project root${NC}"
    exit 1
fi

# Count workflows
workflow_count=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
echo -e "${BLUE}📋 Found $workflow_count workflow files to validate${NC}"
echo ""

# Validate each workflow
validation_failed=false

for workflow_file in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [ -f "$workflow_file" ]; then
        echo -e "${YELLOW}📄 Validating: $(basename "$workflow_file")${NC}"
        
        # Check if file is valid YAML
        if python3 -c "
import yaml
import sys

try:
    with open('$workflow_file', 'r') as f:
        yaml.safe_load(f)
    print('  ✅ Valid YAML syntax')
except yaml.YAMLError as e:
    print(f'  ❌ YAML syntax error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'  ❌ Error reading file: {e}')
    sys.exit(1)
"; then
            echo -e "${GREEN}     ✅ YAML syntax valid${NC}"
        else
            echo -e "${RED}     ❌ YAML syntax error${NC}"
            validation_failed=true
        fi
        
        # Check for common GitHub Actions issues
        echo -e "${BLUE}     🔍 Checking GitHub Actions syntax...${NC}"
        
        # Check for required fields
        if grep -q "^name:" "$workflow_file"; then
            echo -e "${GREEN}       ✅ Has name field${NC}"
        else
            echo -e "${RED}       ❌ Missing name field${NC}"
            validation_failed=true
        fi
        
        if grep -q "^on:" "$workflow_file"; then
            echo -e "${GREEN}       ✅ Has trigger configuration${NC}"
        else
            echo -e "${RED}       ❌ Missing trigger configuration${NC}"
            validation_failed=true
        fi
        
        if grep -q "^jobs:" "$workflow_file"; then
            echo -e "${GREEN}       ✅ Has jobs configuration${NC}"
        else
            echo -e "${RED}       ❌ Missing jobs configuration${NC}"
            validation_failed=true
        fi
        
        # Check for potential issues
        if grep -q "uses: .*@v[0-9]" "$workflow_file"; then
            echo -e "${GREEN}       ✅ Uses pinned action versions${NC}"
        else
            echo -e "${YELLOW}       ⚠️  Consider pinning action versions${NC}"
        fi
        
        echo ""
    fi
done

# Validate dependabot configuration
echo -e "${YELLOW}📄 Validating: .github/dependabot.yml${NC}"
if [ -f ".github/dependabot.yml" ]; then
    if python3 -c "
import yaml
import sys

try:
    with open('.github/dependabot.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check required fields
    if 'version' not in config:
        print('  ❌ Missing version field')
        sys.exit(1)
    
    if 'updates' not in config:
        print('  ❌ Missing updates field')
        sys.exit(1)
    
    print('  ✅ Valid dependabot configuration')
except yaml.YAMLError as e:
    print(f'  ❌ YAML syntax error: {e}')
    sys.exit(1)
"; then
        echo -e "${GREEN}     ✅ Dependabot configuration valid${NC}"
    else
        echo -e "${RED}     ❌ Dependabot configuration error${NC}"
        validation_failed=true
    fi
else
    echo -e "${YELLOW}     ⚠️  No dependabot.yml found${NC}"
fi

echo ""

# Final summary
if [ "$validation_failed" = true ]; then
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo -e "${RED}   Some workflows have configuration errors${NC}"
    echo -e "${YELLOW}   Please fix the errors above before pushing${NC}"
    exit 1
else
    echo -e "${GREEN}✅ ALL WORKFLOWS VALIDATED SUCCESSFULLY${NC}"
    echo -e "${GREEN}   All GitHub Actions configurations are valid${NC}"
    echo -e "${BLUE}   Ready for GitHub integration${NC}"
    exit 0
fi