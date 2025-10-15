#!/bin/bash
################################################################################
# Test Runner for Backup System
#
# Comprehensive test execution script with various options and reporting.
#
# Usage:
#   ./run_tests.sh [OPTIONS]
#
# Options:
#   --unit                Run unit tests only
#   --integration         Run integration tests only
#   --coverage            Generate coverage report
#   --html                Generate HTML coverage report
#   --verbose             Verbose output
#   --fast                Skip slow tests
#   --failed              Re-run only failed tests
#   --markers MARKERS     Run tests with specific markers
#   --file FILE           Run specific test file
#   --clean               Clean test artifacts before running
#
# Examples:
#   ./run_tests.sh                          # Run all tests
#   ./run_tests.sh --unit --coverage        # Unit tests with coverage
#   ./run_tests.sh --integration --verbose  # Integration tests verbose
#   ./run_tests.sh --file test_backup_manager.py  # Single file
################################################################################

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Default options
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_ALL=true
GENERATE_COVERAGE=false
HTML_COVERAGE=false
VERBOSE=false
FAST=false
RE_RUN_FAILED=false
MARKERS=""
SPECIFIC_FILE=""
CLEAN_ARTIFACTS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --html)
            HTML_COVERAGE=true
            GENERATE_COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fast)
            FAST=true
            shift
            ;;
        --failed|--lf)
            RE_RUN_FAILED=true
            shift
            ;;
        --markers|-m)
            MARKERS="$2"
            shift 2
            ;;
        --file|-f)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        --clean)
            CLEAN_ARTIFACTS=true
            shift
            ;;
        --help|-h)
            grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# //g' | sed 's/^#//g'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      ToolboxAI Backup System - Test Runner                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Clean artifacts if requested
if [ "$CLEAN_ARTIFACTS" = true ]; then
    echo -e "${YELLOW}Cleaning test artifacts...${NC}"
    rm -rf htmlcov/ .coverage .pytest_cache/
    rm -f test-report.xml coverage.xml
    echo -e "${GREEN}✓ Artifacts cleaned${NC}"
    echo ""
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found${NC}"
    echo "Install with: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [ "$GENERATE_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=../scripts --cov-report=term-missing"

    if [ "$HTML_COVERAGE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html:htmlcov"
    fi
fi

# Add markers
if [ "$RUN_UNIT" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m unit"
    echo -e "${BLUE}Running unit tests...${NC}"
elif [ "$RUN_INTEGRATION" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m integration"
    echo -e "${BLUE}Running integration tests...${NC}"
elif [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
    echo -e "${BLUE}Running tests with markers: $MARKERS${NC}"
elif [ "$RUN_ALL" = true ]; then
    echo -e "${BLUE}Running all tests...${NC}"
fi

# Skip slow tests if requested
if [ "$FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
    echo -e "${YELLOW}Skipping slow tests${NC}"
fi

# Re-run failed tests
if [ "$RE_RUN_FAILED" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --lf"
    echo -e "${YELLOW}Re-running only failed tests${NC}"
fi

# Run specific file
if [ -n "$SPECIFIC_FILE" ]; then
    PYTEST_CMD="$PYTEST_CMD $SPECIFIC_FILE"
    echo -e "${BLUE}Running tests in: $SPECIFIC_FILE${NC}"
fi

echo ""
echo -e "${YELLOW}Command:${NC} $PYTEST_CMD"
echo ""

# Run tests
START_TIME=$(date +%s)

if $PYTEST_CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                  All Tests Passed! ✓                       ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  Duration: ${DURATION}s                                           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"

    # Display coverage report location if generated
    if [ "$HTML_COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}Coverage report generated:${NC}"
        echo -e "  ${YELLOW}htmlcov/index.html${NC}"
        echo ""
        echo "Open with: open htmlcov/index.html"
    fi

    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                  Tests Failed! ✗                           ║${NC}"
    echo -e "${RED}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${RED}║  Duration: ${DURATION}s                                           ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"

    echo ""
    echo -e "${YELLOW}To re-run only failed tests:${NC}"
    echo "  ./run_tests.sh --failed"

    exit 1
fi
