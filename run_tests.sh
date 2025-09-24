#!/bin/bash

# Comprehensive Test Runner Script for ToolBoxAI-Solutions
# =========================================================
#
# This script provides a simple interface to run the comprehensive test suite
# with proper environment activation and dependency management.
#
# Usage:
#   ./run_tests.sh [OPTIONS]
#
# Options:
#   --install-deps    Install/update pytest dependencies
#   --coverage-only   Run only coverage report generation
#   --quick          Run only unit tests (fast execution)
#   --parallel       Run tests in parallel
#   --verbose        Enable verbose output
#   --debug          Enable debug mode
#   --help           Show this help message

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Function to show help
show_help() {
    echo "Comprehensive Test Runner for ToolBoxAI-Solutions"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install-deps    Install/update pytest dependencies"
    echo "  --coverage-only   Run only coverage report generation"
    echo "  --quick          Run only unit tests (fast execution)"
    echo "  --parallel       Run tests in parallel using pytest-xdist"
    echo "  --verbose        Enable verbose output"
    echo "  --debug          Enable debug mode with detailed logging"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run full test suite"
    echo "  $0 --quick             # Run only unit tests"
    echo "  $0 --install-deps      # Install dependencies and run tests"
    echo "  $0 --parallel --verbose # Run tests in parallel with verbose output"
    exit 0
}

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if help was requested
for arg in "$@"; do
    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        show_help
    fi
done

# Header
echo ""
echo "=================================================================="
print_status "ToolBoxAI-Solutions Comprehensive Test Runner"
echo "=================================================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" || ! -f "pytest.ini" ]]; then
    print_error "This script must be run from the ToolBoxAI-Solutions project root directory"
    print_error "Expected files: pyproject.toml, pytest.ini"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_error "Virtual environment not found at ./venv/"
    print_error "Please create a virtual environment first:"
    print_error "python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check if Python is available
if ! command -v python &> /dev/null; then
    print_error "Python not found in virtual environment"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
print_status "Using Python: $PYTHON_VERSION"

# Check if the comprehensive test runner exists
if [[ ! -f "run_comprehensive_tests.py" ]]; then
    print_error "Comprehensive test runner script not found: run_comprehensive_tests.py"
    exit 1
fi

# Install required dependencies if needed
if [[ "$*" == *"--install-deps"* ]] || ! python -c "import pytest" &>/dev/null; then
    print_status "Installing/updating pytest dependencies..."
    pip install pytest==8.4.2 pytest-asyncio==0.24.0 pytest-cov==6.2.1 pytest-xdist==3.6.1 pytest-timeout==2.3.1 pytest-mock==3.12.0 pytest-html==4.1.1 pytest-json-report==1.5.0 freezegun==1.2.2
    if [[ $? -eq 0 ]]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
fi

# Run the comprehensive test suite
print_status "Starting comprehensive test execution..."
echo ""

# Execute the Python test runner with all arguments
python run_comprehensive_tests.py "$@"
TEST_EXIT_CODE=$?

echo ""
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    print_success "Test execution completed successfully!"
    echo ""
    print_status "Generated Reports:"
    echo "  📊 Test Report: test_report.html"
    echo "  📈 Coverage HTML: htmlcov_comprehensive/index.html"
    echo "  📋 Summary Report: COMPREHENSIVE_TEST_EXECUTION_REPORT.md"
    echo "  📝 Execution Log: test_execution.log"
else
    print_warning "Test execution completed with issues"
    echo ""
    print_status "Check the following for details:"
    echo "  📊 Test Report: test_report.html"
    echo "  📋 Summary Report: COMPREHENSIVE_TEST_EXECUTION_REPORT.md"
    echo "  📝 Execution Log: test_execution.log"
fi

echo ""
print_status "Test execution completed. Exit code: $TEST_EXIT_CODE"
echo "=================================================================="

exit $TEST_EXIT_CODE