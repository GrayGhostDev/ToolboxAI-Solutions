#!/bin/bash

# E2E Test Runner for ToolBoxAI Dashboard
# Handles Playwright installation and test execution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎭 ToolBoxAI Dashboard E2E Test Runner"
echo "======================================"
echo ""

# Check if Playwright is installed
if ! npm list @playwright/test >/dev/null 2>&1; then
    echo "📦 Installing Playwright..."
    npm install -D @playwright/test @axe-core/playwright
    echo "✅ Playwright installed"
    echo ""

    echo "🌐 Installing Playwright browsers..."
    npx playwright install chromium firefox webkit
    echo "✅ Browsers installed"
    echo ""
else
    echo "✅ Playwright is already installed"
    echo ""
fi

# Function to start backend if not running
start_backend_if_needed() {
    if ! curl -s -f http://localhost:8009/health >/dev/null 2>&1; then
        echo "🚀 Backend should be running in Docker on port 8009"
        echo "   Checking Docker container status..."

        # Check if Docker container is running
        if docker ps | grep -q "toolboxai-fastapi"; then
            echo "✅ Backend Docker container is running"
        else
            echo "❌ Backend Docker container is not running"
            echo "   Please start Docker services with: docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d"
            return 1
        fi

        # Wait for backend to be ready
        echo "   Waiting for backend to be ready..."
        for i in {1..30}; do
            if curl -s -f http://localhost:8009/health >/dev/null 2>&1; then
                echo "✅ Backend is ready on port 8009"
                return 0
            fi
            sleep 1
        done

        echo "❌ Backend is not responding on port 8009"
        return 1
    else
        echo "✅ Backend is already running on port 8009"
        BACKEND_PID=""
    fi
}

# Function to start dashboard if not running
start_dashboard_if_needed() {
    if ! curl -s -f http://localhost:5179 >/dev/null 2>&1; then
        echo "🚀 Starting dashboard..."
        npm run dev &
        DASHBOARD_PID=$!
        echo "   Dashboard PID: $DASHBOARD_PID"

        # Wait for dashboard to be ready
        echo "   Waiting for dashboard to be ready..."
        for i in {1..30}; do
            if curl -s -f http://localhost:5179 >/dev/null 2>&1; then
                echo "✅ Dashboard is ready"
                return 0
            fi
            sleep 1
        done

        echo "❌ Dashboard failed to start"
        return 1
    else
        echo "✅ Dashboard is already running"
        DASHBOARD_PID=""
    fi
}

# Parse command line arguments
TEST_TYPE="all"
HEADED=false
DEBUG=false
UI=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auth)
            TEST_TYPE="auth"
            shift
            ;;
        --admin)
            TEST_TYPE="admin"
            shift
            ;;
        --realtime)
            TEST_TYPE="realtime"
            shift
            ;;
        --accessibility)
            TEST_TYPE="accessibility"
            shift
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --ui)
            UI=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --auth           Run authentication tests only"
            echo "  --admin          Run admin dashboard tests only"
            echo "  --realtime       Run real-time Pusher tests only"
            echo "  --accessibility  Run accessibility tests only"
            echo "  --headed         Run tests in headed mode (show browser)"
            echo "  --debug          Run tests in debug mode"
            echo "  --ui             Open Playwright Test UI"
            echo "  --help           Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Start services if needed
start_backend_if_needed
start_dashboard_if_needed

echo ""
echo "🧪 Running E2E Tests"
echo "===================="

# Build Playwright command
PLAYWRIGHT_CMD="npx playwright test"

# Add test filter based on type
case $TEST_TYPE in
    auth)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD e2e/tests/auth"
        echo "Testing: Authentication flows"
        ;;
    admin)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD e2e/tests/admin"
        echo "Testing: Admin dashboard"
        ;;
    realtime)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD e2e/tests/realtime"
        echo "Testing: Real-time updates"
        ;;
    accessibility)
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=accessibility"
        echo "Testing: Accessibility"
        ;;
    all)
        echo "Testing: All test suites"
        ;;
esac

# Add mode flags
if [ "$HEADED" = true ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --headed"
    echo "Mode: Headed (browser visible)"
fi

if [ "$DEBUG" = true ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --debug"
    echo "Mode: Debug"
fi

if [ "$UI" = true ]; then
    PLAYWRIGHT_CMD="npx playwright test --ui"
    echo "Mode: UI"
fi

echo ""

# Run tests
set +e
$PLAYWRIGHT_CMD
TEST_EXIT_CODE=$?
set -e

# Cleanup
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."

    if [ ! -z "$BACKEND_PID" ]; then
        echo "   Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$DASHBOARD_PID" ]; then
        echo "   Stopping dashboard (PID: $DASHBOARD_PID)..."
        kill $DASHBOARD_PID 2>/dev/null || true
    fi

    echo "✅ Cleanup complete"
}

# Register cleanup on exit
trap cleanup EXIT

# Show results
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"

    # Offer to show report
    echo ""
    echo "📊 View test report with:"
    echo "   npx playwright show-report"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
    echo ""
    echo "📊 View detailed report with:"
    echo "   npx playwright show-report"
    echo ""
    echo "🔍 Debug failed tests with:"
    echo "   $0 --debug"
fi

exit $TEST_EXIT_CODE