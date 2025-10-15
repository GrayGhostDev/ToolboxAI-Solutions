#!/bin/bash

# ToolboxAI basic Docker startup helper
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_DIR="$PROJECT_ROOT/infrastructure/docker/compose"
COMPOSE_FILES=(-f "$COMPOSE_DIR/docker-compose.yml" -f "$COMPOSE_DIR/docker-compose.dev.yml")

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "❌ docker compose not available. Install Docker Desktop 4.29+." >&2
  exit 1
fi

COMPOSE_DISPLAY="${COMPOSE_CMD[*]}"

compose() {
  "${COMPOSE_CMD[@]}" "${COMPOSE_FILES[@]}" "$@"
}

echo "🚀 Starting ToolboxAI Docker services from $PROJECT_ROOT"

check_health() {
  local service="$1"
  local max_attempts=30
  local attempt=1

  echo "⏳ Waiting for $service to report healthy..."
  while [ "$attempt" -le "$max_attempts" ]; do
    if compose ps --format '{{.Service}}\t{{.Health}}' 2>/dev/null | grep -E "^${service}\s+healthy$" >/dev/null; then
      echo "✅ $service is healthy"
      return 0
    fi
    sleep 2
    attempt=$((attempt + 1))
  done

  echo "❌ $service did not become healthy in time"
  return 1
}

echo "🧹 Cleaning up previous containers (if any)..."
compose down --remove-orphans >/dev/null 2>&1 || true

echo "📦 Starting data services (postgres, redis)..."
compose up -d postgres redis 2>&1 | grep -v "variable is not set" || true
check_health "postgres" || true
check_health "redis" || true

echo "🔨 Building and starting backend..."
compose up -d --build backend 2>&1 | grep -v "variable is not set" || true
check_health "backend" || true

echo "🤖 Starting orchestration services..."
compose up -d mcp-server agent-coordinator 2>&1 | grep -v "variable is not set" || true
check_health "mcp-server" || true
check_health "agent-coordinator" || true

echo "📮 Starting background workers..."
compose up -d celery-worker celery-beat flower 2>&1 | grep -v "variable is not set" || true

echo "🖥️ Starting dashboard and tooling..."
compose up -d dashboard adminer redis-commander mailhog 2>&1 | grep -v "variable is not set" || true
check_health "dashboard" || true

echo ""
echo "📊 Current service status:"
compose ps

echo ""
echo "🔍 Common URLs:"
cat <<EOF
  Backend API:       http://localhost:8009
  API Docs:          http://localhost:8009/docs
  Dashboard (Vite):  http://localhost:5179
  MCP Server:        http://localhost:9877
  Agent Coordinator: http://localhost:8888
  Flower:            http://localhost:5555
  Adminer:           http://localhost:8080
  Redis Commander:   http://localhost:8081
  Mailhog:           http://localhost:8025
EOF

echo ""
echo "📝 Logs: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} logs -f <service>"
echo "🛑 Stop: $COMPOSE_DISPLAY ${COMPOSE_FILES[*]} down"
