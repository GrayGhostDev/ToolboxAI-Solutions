#!/bin/bash
# Terminal 2: Frontend Dashboard
# Manages React dashboard development server

echo "========================================="
echo "Terminal 2: Frontend Dashboard Manager"
echo "========================================="

cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Wait for backend to be ready
echo "⏳ Waiting for backend services..."
python3 scripts/terminal_coordinator.py frontend &
sleep 2

# Check if backend is available
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://127.0.0.1:8008/health > /dev/null 2>&1; then
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
    exit 1
fi

# Setup frontend
echo "📦 Setting up frontend dashboard..."
cd src/dashboard

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
    echo "📦 Installing npm packages..."
    npm install
fi

# Kill any existing process on port 5177
lsof -ti:5177 | xargs -r kill -9 2>/dev/null || true

# Start the development server
echo "🚀 Starting dashboard development server..."
npm run dev &
DASHBOARD_PID=$!

# Wait for dashboard to be ready
sleep 5

echo "
========================================="
echo "Terminal 2 Ready!"
echo "========================================="
echo "Services running:"
echo "  - Dashboard: http://localhost:5177"
echo "  - Backend API: http://127.0.0.1:8008"
echo ""
echo "Dashboard Features:"
echo "  ✓ Real-time WebSocket connection"
echo "  ✓ Socket.io integration"
echo "  ✓ Live data updates"
echo "  ✓ Authentication system"
echo ""
echo "To test the dashboard:"
echo "  1. Open http://localhost:5177 in browser"
echo "  2. Login with test credentials"
echo "  3. Check browser console for errors"
echo "========================================="

# Keep terminal alive
wait $DASHBOARD_PID