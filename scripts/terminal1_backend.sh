#!/usr/bin/env sh
# Terminal 1: Backend Services
# Manages database setup and backend API servers
set -eu
# shellcheck source=common/lib.sh
. "$(cd "$(dirname "$0")"/.. && pwd -P)/scripts/common/lib.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")"/.. && pwd -P)/common/lib.sh"

echo "========================================="
echo "Terminal 1: Backend Services Manager"
echo "========================================="

cd "$PROJECT_ROOT"

# Use coordinator to prevent conflicts
python3 scripts/terminal_coordinator.py backend setup_database || true

echo "📦 Setting up database..."
if [ -d "database" ]; then
  cd database
  if [ ! -f ".db_initialized" ]; then
      [ -f setup_database.py ] && python3 setup_database.py || true
      [ -f create_initial_data.py ] && python3 create_initial_data.py || true
      touch .db_initialized
      echo "✓ Database initialized"
  else
      echo "✓ Database already initialized"
  fi
  cd ..
else
  echo "⚠️  database/ directory not found; skipping setup"
fi

# Mark database setup complete
python3 scripts/terminal_coordinator.py backend start_fastapi_server || true

echo "🚀 Starting FastAPI server with Socket.io..."
cd "$PROJECT_ROOT/ToolboxAI-Roblox-Environment"

# Kill any existing processes on configured port
lsof -ti:"$FASTAPI_PORT" | xargs -r kill -9 2>/dev/null || true

# Activate virtual environment
if [ -f "venv_clean/bin/activate" ]; then
  # shellcheck disable=SC1091
  . venv_clean/bin/activate
else
  die "venv_clean not found. Please set up the environment first."
fi

# Start the server with Socket.io support (env-only; no inline secrets)
LOG_FILE="$PROJECT_ROOT/logs/fastapi_server.log"
uvicorn server.main:socketio_app \
  --host "$API_HOST" \
  --port "$FASTAPI_PORT" \
  --reload \
  >"$LOG_FILE" 2>&1 &
FASTAPI_PID=$!
write_pid "FastAPI-Server" "$FASTAPI_PID"

echo "✓ FastAPI server started on http://$API_HOST:$FASTAPI_PORT (PID: $FASTAPI_PID)"

# Ensure cleanup on exit
trap 'log "Stopping FastAPI (PID $FASTAPI_PID)"; kill $FASTAPI_PID 2>/dev/null || true; stop_by_pid FastAPI-Server' INT TERM EXIT

# Wait for server to be ready
sleep 5 || true

# Test server health
echo "🔍 Testing server health..."
if command -v curl >/dev/null 2>&1; then
  curl -s "http://$API_HOST:$FASTAPI_PORT/health" >/dev/null 2>&1 && echo "✓ Health OK" || echo "⚠️ Health check failed"
fi

# Mark task complete
python3 "$PROJECT_ROOT/scripts/terminal_coordinator.py" backend start_socketio_server || true

echo "
========================================="
echo "Terminal 1 Ready!"
echo "========================================="
echo "Services running:"
echo "  - FastAPI + Socket.io: http://$API_HOST:$FASTAPI_PORT"
echo "  - API Docs: http://$API_HOST:$FASTAPI_PORT/docs"
echo "  - Socket.io: ws://$API_HOST:$FASTAPI_PORT/socket.io/"
echo ""
echo "Next steps for other terminals:"
echo "  Terminal 2: Run frontend dashboard"
echo "  Terminal 3: Run Roblox bridge server"
echo "  Terminal 4: Run tests"
echo "========================================="

# Keep terminal alive
wait $FASTAPI_PID
