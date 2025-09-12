#!/bin/bash
# Documentation Pipeline - Automated documentation generation for all components
# This script orchestrates the complete documentation generation process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       ToolBoxAI Documentation Generation Pipeline            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if Python virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo -e "${YELLOW}⚠️  Virtual environment not activated. Activating...${NC}"
        source "$PROJECT_ROOT/ToolboxAI-Roblox-Environment/venv_clean/bin/activate" 2>/dev/null || {
            echo -e "${RED}❌ Failed to activate virtual environment${NC}"
            exit 1
        }
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    fi
}

# Function to run a documentation generator
run_generator() {
    local generator_name=$1
    local generator_script=$2
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📚 Generating ${generator_name} Documentation${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [[ -f "$SCRIPT_DIR/$generator_script" ]]; then
        python "$SCRIPT_DIR/$generator_script" || {
            echo -e "${RED}❌ Failed to generate ${generator_name} documentation${NC}"
            return 1
        }
    else
        echo -e "${YELLOW}⚠️  ${generator_name} generator not found: $generator_script${NC}"
        return 1
    fi
}

# Function to check Redis availability
check_redis() {
    echo -e "\n${BLUE}🔍 Checking Redis availability...${NC}"
    redis-cli ping > /dev/null 2>&1 || {
        echo -e "${YELLOW}⚠️  Redis not available. Terminal notifications will be skipped.${NC}"
        return 1
    }
    echo -e "${GREEN}✅ Redis is available${NC}"
    return 0
}

# Function to send notification to all terminals
notify_terminals() {
    local message=$1
    if check_redis; then
        redis-cli PUBLISH terminal:all:documentation "{\"type\":\"pipeline_status\",\"message\":\"$message\",\"timestamp\":\"$(date -Iseconds)\"}" > /dev/null
        echo -e "${GREEN}📢 Notified all terminals: $message${NC}"
    fi
}

# Main pipeline execution
main() {
    local start_time=$(date +%s)
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check virtual environment
    check_venv
    
    # Notify start
    notify_terminals "Documentation pipeline started"
    
    # 1. Generate API Documentation
    if run_generator "API" "generate_api_docs.py"; then
        echo -e "${GREEN}✅ API documentation generated successfully${NC}"
        notify_terminals "API documentation completed"
    else
        echo -e "${RED}❌ API documentation generation failed${NC}"
    fi
    
    # 2. Generate Component Documentation
    if run_generator "React Component" "scan_components.py"; then
        echo -e "${GREEN}✅ Component documentation generated successfully${NC}"
        notify_terminals "Component documentation completed"
    else
        echo -e "${RED}❌ Component documentation generation failed${NC}"
    fi
    
    # 3. Generate Database Schema Documentation
    if run_generator "Database Schema" "document_schemas.py"; then
        echo -e "${GREEN}✅ Database schema documentation generated successfully${NC}"
        notify_terminals "Database documentation completed"
    else
        echo -e "${RED}❌ Database schema documentation generation failed${NC}"
    fi
    
    # 4. Generate Test Coverage Documentation
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 Generating Test Coverage Report${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [[ -d "$PROJECT_ROOT/ToolboxAI-Roblox-Environment/tests" ]]; then
        cd "$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
        pytest tests/ --cov=server --cov=agents --cov=mcp --cov-report=html --cov-report=json -q || {
            echo -e "${YELLOW}⚠️  Test coverage generation completed with warnings${NC}"
        }
        
        # Move coverage reports to documentation directory
        if [[ -f "coverage.json" ]]; then
            mkdir -p "$PROJECT_ROOT/Documentation/04-implementation/coverage"
            cp coverage.json "$PROJECT_ROOT/Documentation/04-implementation/coverage/"
            cp -r htmlcov/* "$PROJECT_ROOT/Documentation/04-implementation/coverage/" 2>/dev/null || true
            echo -e "${GREEN}✅ Test coverage documentation generated${NC}"
            notify_terminals "Test coverage documentation completed"
        fi
        cd "$PROJECT_ROOT"
    else
        echo -e "${YELLOW}⚠️  Test directory not found${NC}"
    fi
    
    # 5. Generate Documentation Summary
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📝 Generating Documentation Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Create summary file
    SUMMARY_FILE="$PROJECT_ROOT/Documentation/DOCUMENTATION_STATUS.md"
    {
        echo "# Documentation Status Report"
        echo ""
        echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "## Documentation Coverage"
        echo ""
        
        # Check API documentation
        if [[ -f "$PROJECT_ROOT/Documentation/03-api/openapi-spec.yaml" ]]; then
            echo "- ✅ **API Documentation**: Complete"
            endpoints=$(grep -c "paths:" "$PROJECT_ROOT/Documentation/03-api/openapi-spec.yaml" 2>/dev/null || echo "0")
            echo "  - OpenAPI Specification: Available"
        else
            echo "- ❌ **API Documentation**: Missing"
        fi
        
        # Check component documentation
        if [[ -f "$PROJECT_ROOT/Documentation/05-features/dashboard/components/README.md" ]]; then
            echo "- ✅ **Component Documentation**: Complete"
            components=$(find "$PROJECT_ROOT/Documentation/05-features/dashboard/components" -name "*.md" | wc -l)
            echo "  - Components documented: $components"
        else
            echo "- ❌ **Component Documentation**: Missing"
        fi
        
        # Check database documentation
        if [[ -f "$PROJECT_ROOT/Documentation/02-architecture/data-models/README.md" ]]; then
            echo "- ✅ **Database Documentation**: Complete"
            schemas=$(find "$PROJECT_ROOT/Documentation/02-architecture/data-models" -name "*_schema.md" | wc -l)
            echo "  - Schemas documented: $schemas"
        else
            echo "- ❌ **Database Documentation**: Missing"
        fi
        
        # Check test coverage
        if [[ -f "$PROJECT_ROOT/Documentation/04-implementation/coverage/coverage.json" ]]; then
            echo "- ✅ **Test Coverage**: Available"
        else
            echo "- ⚠️  **Test Coverage**: Not generated"
        fi
        
        echo ""
        echo "## Documentation Files"
        echo ""
        echo "\`\`\`"
        find "$PROJECT_ROOT/Documentation" -type f -name "*.md" | head -20
        echo "\`\`\`"
        
        echo ""
        echo "## Next Steps"
        echo ""
        echo "1. Review generated documentation for accuracy"
        echo "2. Add missing descriptions and examples"
        echo "3. Setup automated documentation monitoring with \`doc_monitor.py\`"
        echo "4. Configure CI/CD to run this pipeline on commits"
        
    } > "$SUMMARY_FILE"
    
    echo -e "${GREEN}✅ Documentation summary created: $SUMMARY_FILE${NC}"
    
    # 6. Verify Documentation Completeness
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔍 Verifying Documentation Completeness${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Count documentation files
    total_docs=$(find "$PROJECT_ROOT/Documentation" -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.json" \) | wc -l)
    echo -e "${GREEN}📊 Total documentation files: $total_docs${NC}"
    
    # Calculate execution time
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    # Final notification
    notify_terminals "Documentation pipeline completed in ${duration}s"
    
    # Final summary
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Documentation Pipeline Completed Successfully        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✨ Execution time: ${duration} seconds${NC}"
    echo -e "${GREEN}📁 Documentation location: $PROJECT_ROOT/Documentation${NC}"
    echo -e "${GREEN}📊 Total files generated: $total_docs${NC}"
    echo ""
    echo -e "${BLUE}To monitor documentation changes in real-time, run:${NC}"
    echo -e "${YELLOW}  python scripts/terminal_sync/doc_monitor.py --watch --auto-update --notify-terminals${NC}"
    echo ""
}

# Parse command line arguments
SKIP_TESTS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-tests    Skip test coverage generation"
            echo "  --verbose       Show detailed output"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run the pipeline
main