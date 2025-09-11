#!/usr/bin/env sh
# Terminal 2: Frontend Dashboard
# Manages React dashboard development server
set -eu
# shellcheck source=common/lib.sh
. "$(cd "$(dirname "$0")"/.. && pwd -P)/scripts/common/lib.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")"/.. && pwd -P)/common/lib.sh"

echo "========================================="
echo "Terminal 2: Frontend Dashboard Manager"
echo "========================================="

cd "$PROJECT_ROOT"

# Wait for backend to be ready (optional)
echo "⏳ Waiting for backend services..."
python3 scripts/terminal_coordinator.py frontend || true
sleep 2 || true

# Check if backend is available
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "http://$API_HOST:$FASTAPI_PORT/health" > /dev/null 2>&1; then
        echo "✓ Backend is ready!"
        break
    fi
    echo "  Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️ Backend not available after $MAX_RETRIES attempts"
    echo "Please ensure Terminal 1 (backend) is running first"
fi

# Setup frontend
echo "📦 Setting up frontend dashboard..."
cd src/dashboard

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
    echo "📦 Installing npm packages..."
    npm install
fi

# Kill any existing process on the canonical port
lsof -ti:"$DASHBOARD_PORT" | xargs -r kill -9 2>/dev/null || true

# Start the development server on canonical port
echo "🚀 Starting dashboard development server on port $DASHBOARD_PORT..."
HOST="$API_HOST" PORT="$DASHBOARD_PORT" npm run dev &
DASHBOARD_PID=$!

# Wait for dashboard to be ready
sleep 5 || true

echo "
========================================="
echo "Terminal 2 Ready!"
echo "========================================="
echo "Services running:"
echo "  - Dashboard: http://$API_HOST:$DASHBOARD_PORT"
echo "  - Backend API: http://$API_HOST:$FASTAPI_PORT"
echo ""
echo "Dashboard Features:"
echo "  ✓ Real-time WebSocket connection"
echo "  ✓ Socket.io integration"
echo "  ✓ Live data updates"
echo "  ✓ Authentication system"
echo ""
echo "To test the dashboard:"
echo "  1. Open http://$API_HOST:$DASHBOARD_PORT in browser"
echo "  2. Login with test credentials"
echo "  3. Check browser console for errors"
echo "========================================="

# Ensure cleanup on exit
trap 'log "Stopping dashboard (PID $DASHBOARD_PID)"; kill $DASHBOARD_PID 2>/dev/null || true' INT TERM EXIT

# Keep terminal alive
wait $DASHBOARD_PID
