#!/bin/bash
# Terminal 1: Backend Services
# Manages database setup and backend API servers

echo "========================================="
echo "Terminal 1: Backend Services Manager"
echo "========================================="

cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Use coordinator to prevent conflicts
python3 scripts/terminal_coordinator.py backend setup_database

echo "📦 Setting up database..."
cd database
if [ ! -f ".db_initialized" ]; then
    python3 setup_database.py
    python3 create_initial_data.py
    touch .db_initialized
    echo "✓ Database initialized"
else
    echo "✓ Database already initialized"
fi
cd ..

# Mark database setup complete
python3 scripts/terminal_coordinator.py backend start_fastapi_server

echo "🚀 Starting FastAPI server with Socket.io..."
cd ToolboxAI-Roblox-Environment

# Kill any existing processes on port 8008
lsof -ti:8008 | xargs -r kill -9 2>/dev/null || true

# Start the server with Socket.io support
export POSTGRES_PASSWORD=staging_password_2024
export REDIS_PASSWORD=staging_redis_2024
export JWT_SECRET_KEY=staging_jwt_secret_key_very_long_and_secure_2024
export SENTRY_DSN="https://af64bfdc2bd0cd6cd870bfeb7f26c22c@o4509912543199232.ingest.us.sentry.io/4509991438581760"
export SENTRY_ENVIRONMENT=staging
export SENTRY_TRACES_SAMPLE_RATE=1.0
export ENVIRONMENT=staging
export DEBUG=True

source venv_clean/bin/activate
uvicorn server.main:socketio_app --host 127.0.0.1 --port 8008 --reload &
FASTAPI_PID=$!

echo "✓ FastAPI server started on port 8008 (PID: $FASTAPI_PID)"

# Wait for server to be ready
sleep 5

# Test server health
echo "🔍 Testing server health..."
curl -s http://127.0.0.1:8008/health | jq . || echo "⚠️ Server health check failed"

# Mark task complete
python3 ../scripts/terminal_coordinator.py backend start_socketio_server

echo "
========================================="
echo "Terminal 1 Ready!"
echo "========================================="
echo "Services running:"
echo "  - FastAPI + Socket.io: http://127.0.0.1:8008"
echo "  - API Docs: http://127.0.0.1:8008/docs"
echo "  - Socket.io: ws://127.0.0.1:8008/socket.io/"
echo ""
echo "Next steps for other terminals:"
echo "  Terminal 2: Run frontend dashboard"
echo "  Terminal 3: Run Roblox bridge server"
echo "  Terminal 4: Run tests"
echo "========================================="

# Keep terminal alive
wait $FASTAPI_PID