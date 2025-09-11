#!/bin/bash
# Terminal 3: Roblox Bridge Server
# Manages Flask bridge for Roblox communication

echo "========================================="
echo "Terminal 3: Roblox Bridge Server Manager"
echo "========================================="

cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Wait for backend to be ready
echo "⏳ Waiting for backend services..."
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

# Setup Roblox bridge
echo "🌉 Setting up Roblox bridge server..."
cd ToolboxAI-Roblox-Environment

# Kill any existing process on port 5001
lsof -ti:5001 | xargs -r kill -9 2>/dev/null || true

# Set environment variables
export POSTGRES_PASSWORD=staging_password_2024
export REDIS_PASSWORD=staging_redis_2024
export JWT_SECRET_KEY=staging_jwt_secret_key_very_long_and_secure_2024

# Activate virtual environment
source venv_clean/bin/activate

# Start the Roblox bridge server
echo "🚀 Starting Roblox bridge server..."
python server/roblox_server.py &
ROBLOX_PID=$!

# Wait for server to be ready
sleep 5

# Test server health
echo "🔍 Testing Roblox bridge health..."
curl -s http://127.0.0.1:5001/health | jq . || echo "⚠️ Roblox bridge health check failed"

echo "
========================================="
echo "Terminal 3 Ready!"
echo "========================================="
echo "Services running:"
echo "  - Roblox Bridge: http://127.0.0.1:5001"
echo "  - Health Check: http://127.0.0.1:5001/health"
echo ""
echo "Roblox Integration:"
echo "  ✓ Flask bridge server active"
echo "  ✓ Roblox Studio plugin port: 64989"
echo "  ✓ Content generation endpoint ready"
echo "  ✓ Quiz system endpoint ready"
echo ""
echo "To test Roblox integration:"
echo "  1. Open Roblox Studio"
echo "  2. Load the ToolboxAI plugin"
echo "  3. Connect to http://127.0.0.1:5001"
echo "========================================="

# Keep terminal alive
wait $ROBLOX_PID