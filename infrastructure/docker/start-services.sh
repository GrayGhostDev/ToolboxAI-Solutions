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

DEFAULT_PROFILES="week2,production,migration"
if [[ -z "${COMPOSE_PROFILES:-}" ]]; then
  export COMPOSE_PROFILES="$DEFAULT_PROFILES"
  echo "ℹ️  COMPOSE_PROFILES not set. Enabling profiles: $COMPOSE_PROFILES"
fi

AVAILABLE_SERVICES=""
SERVICE_FILTER_DISABLED=false
if ! AVAILABLE_SERVICES="$(compose config --services 2>/dev/null)"; then
  SERVICE_FILTER_DISABLED=true
  echo "⚠️  Could not resolve compose service list; attempting to start all phases regardless."
fi

service_exists() {
  local service="$1"
  if [[ "$SERVICE_FILTER_DISABLED" == true ]]; then
    return 0
  fi
  printf '%s\n' "$AVAILABLE_SERVICES" | grep -qx "$service"
}

NEEDS_HEALTHCHECK=(postgres redis backend mcp-server agent-coordinator dashboard celery-flower)
needs_healthcheck() {
  local service="$1"
  for target in "${NEEDS_HEALTHCHECK[@]}"; do
    if [[ "$service" == "$target" ]]; then
      return 0
    fi
  done
  return 1
}

start_single_service() {
  local service="$1"
  if ! service_exists "$service"; then
    echo "⚪️  Skipping $service (not defined in current compose files)"
    return 0
  fi

  echo "▶️  Starting $service..."
  local extra_args=()
  if [[ "$service" == "backend" || "$service" == "dashboard" ]]; then
    extra_args+=(--build)
  fi
  if ! compose up -d "${extra_args[@]}" "$service"; then
    echo "❌ Failed to start $service"
    return 1
  fi

  if needs_healthcheck "$service"; then
    check_health "$service" || true
  fi
}

start_phase() {
  local phase_title="$1"
  shift
  echo ""
  echo "=== $phase_title ==="
  for service in "$@"; do
    start_single_service "$service"
  done
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

start_phase "Phase 1: Core data services" postgres redis
start_phase "Phase 2: Application backends" backend mcp-server agent-coordinator
start_phase "Phase 3: Async workers & monitoring" celery-worker celery-beat celery-flower flower
start_phase "Phase 4: Extended stack" roblox-sync redis-cloud-connector backup-coordinator migration-runner prometheus
start_phase "Phase 5: Frontend & tooling" dashboard adminer redis-commander mailhog

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
