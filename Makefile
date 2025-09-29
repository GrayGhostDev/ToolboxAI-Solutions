# ToolboxAI-Solutions Makefile

.PHONY: dev backend dashboard test lint build

# Default ports
API_HOST ?= 127.0.0.1
API_PORT ?= 8009
DASHBOARD_PORT ?= 5179

# Python
PY ?= python3
UVICORN ?= uvicorn

backend:
	$(UVICORN) apps.backend.main:app --host $(API_HOST) --port $(API_PORT) --reload

dashboard:
	npm run dashboard:dev

dev:
	@echo "Starting backend (FastAPI) and dashboard (Vite)"
	@echo "Backend: http://$(API_HOST):$(API_PORT)"
	@echo "Dashboard: http://127.0.0.1:$(DASHBOARD_PORT)"
	( $(MAKE) backend & ) ; ( $(MAKE) dashboard )

lint:
	@echo "Python lint: black + mypy (skipped if not installed)"
	- black apps/backend || true
	- mypy apps/backend || true
	@echo "JS/TS lint: eslint"
	npm -w apps/dashboard run lint || true

test:
	@echo "Python tests"
	pytest -q || true
	@echo "Dashboard tests"
	npm -w apps/dashboard test || true

build:
	npm -w apps/dashboard run build

# ============================================
# DOCKER COMMANDS
# ============================================
DOCKER_DIR = infrastructure/docker/compose
COMPOSE_BASE = docker compose -f $(DOCKER_DIR)/docker-compose.yml
COMPOSE_DEV = $(COMPOSE_BASE) -f $(DOCKER_DIR)/docker-compose.dev.yml
COMPOSE_PROD = $(COMPOSE_BASE) -f $(DOCKER_DIR)/docker-compose.prod.yml
COMPOSE_MONITORING = $(COMPOSE_BASE) -f $(DOCKER_DIR)/docker-compose.monitoring.yml

# Docker Development Commands
docker-dev:
	@echo "Starting all services in development mode..."
	$(COMPOSE_DEV) up -d

docker-dev-build:
	@echo "Building and starting all services in development mode..."
	$(COMPOSE_DEV) up -d --build

docker-dev-logs:
	$(COMPOSE_DEV) logs -f

docker-dev-stop:
	$(COMPOSE_DEV) stop

docker-dev-down:
	$(COMPOSE_DEV) down

docker-dev-clean:
	$(COMPOSE_DEV) down -v

# Docker Production Commands
docker-prod:
	@echo "Starting all services in production mode..."
	$(COMPOSE_PROD) up -d

docker-prod-build:
	$(COMPOSE_PROD) up -d --build

docker-prod-logs:
	$(COMPOSE_PROD) logs -f

docker-prod-stop:
	$(COMPOSE_PROD) stop

docker-prod-down:
	$(COMPOSE_PROD) down

# Docker Monitoring Stack
docker-monitoring:
	@echo "Starting monitoring stack (Grafana, Loki, Jaeger)..."
	$(COMPOSE_DEV) -f $(DOCKER_DIR)/docker-compose.monitoring.yml up -d

docker-monitoring-down:
	$(COMPOSE_DEV) -f $(DOCKER_DIR)/docker-compose.monitoring.yml down

# Celery Commands
celery-worker:
	@echo "Starting Celery worker (Celery 5.4)..."
	$(COMPOSE_DEV) up -d celery-worker
	@echo "✓ Worker started. View logs: make celery-logs"

celery-beat:
	@echo "Starting Celery beat scheduler..."
	$(COMPOSE_DEV) up -d celery-beat
	@echo "✓ Beat scheduler running for periodic tasks"

celery-flower:
	@echo "Starting Celery Flower monitoring dashboard..."
	$(COMPOSE_DEV) up -d celery-flower
	@echo "✓ Flower dashboard available at: http://localhost:5555"

celery-logs:
	$(COMPOSE_DEV) logs -f celery-worker celery-beat

celery-status:
	@echo "Checking Celery workers status..."
	@docker exec $$(docker ps -q -f name=celery-worker | head -1) celery -A apps.backend.celery_app inspect active || echo "No active workers"

celery-purge:
	@echo "⚠️  Purging all pending tasks from queue..."
	@docker exec $$(docker ps -q -f name=celery-worker | head -1) celery -A apps.backend.celery_app purge -f
	@echo "✓ Queue purged"

# Start complete Celery stack
celery-up: celery-worker celery-beat celery-flower
	@echo "✓ Complete Celery stack running"
	@echo "  - Worker: Processing tasks"
	@echo "  - Beat: Scheduling periodic tasks"
	@echo "  - Flower: http://localhost:5555"

# Stop all Celery services
celery-down:
	@echo "Stopping all Celery services..."
	$(COMPOSE_DEV) stop celery-worker celery-beat celery-flower
	@echo "✓ Celery services stopped"

# Roblox Services
roblox-sync:
	$(COMPOSE_DEV) up -d roblox-sync

roblox-logs:
	$(COMPOSE_DEV) logs -f roblox-sync

rojo-serve:
	docker exec toolboxai-roblox-sync rojo serve --project /app/default.project.json

# Database Commands
db-shell:
	docker exec -it toolboxai-postgres psql -U toolboxai -d toolboxai

redis-cli:
	docker exec -it toolboxai-redis redis-cli

# Monitoring Access URLs
urls:
	@echo "==================================="
	@echo "Service URLs:"
	@echo "==================================="
	@echo "Backend API:        http://localhost:8009"
	@echo "Dashboard:          http://localhost:5179"
	@echo "Flower (Celery):    http://localhost:5555"
	@echo "Grafana:           http://localhost:3000"
	@echo "Prometheus:        http://localhost:9090"
	@echo "Jaeger UI:         http://localhost:16686"
	@echo "Loki:              http://localhost:3100"
	@echo "Alertmanager:      http://localhost:9093"
	@echo "Adminer (DB):      http://localhost:8080"
	@echo "Redis Commander:   http://localhost:8081"
	@echo "Rojo Server:       http://localhost:34872"
	@echo "Mailhog:           http://localhost:8025"
	@echo "==================================="

# Health Checks
health:
	@echo "Checking service health..."
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep toolboxai

# Full Stack Commands
stack-up: docker-dev docker-monitoring
	@echo "Full stack started!"
	@make urls

stack-down: docker-dev-down docker-monitoring-down
	@echo "Full stack stopped!"

stack-clean: docker-dev-clean
	@echo "All volumes and containers removed!"

# Docker Secrets (Production)
docker-secrets-create:
	@echo "Creating Docker secrets..."
	@echo "Enter database password:" && read -s DB_PASS && echo $$DB_PASS | docker secret create db_password -
	@echo "Enter Redis password:" && read -s REDIS_PASS && echo $$REDIS_PASS | docker secret create redis_password -
	@echo "Enter JWT secret:" && read -s JWT_SECRET && echo $$JWT_SECRET | docker secret create jwt_secret -
	@echo "Secrets created!"

# Help
docker-help:
	@echo "Docker Commands:"
	@echo "  make docker-dev         - Start development environment"
	@echo "  make docker-dev-build   - Build and start development"
	@echo "  make docker-dev-logs    - View development logs"
	@echo "  make docker-dev-stop    - Stop development services"
	@echo "  make docker-dev-down    - Remove development containers"
	@echo "  make docker-monitoring  - Start monitoring stack"
	@echo "  make celery-worker      - Start Celery worker"
	@echo "  make celery-flower      - Start Flower monitoring"
	@echo "  make roblox-sync        - Start Roblox sync service"
	@echo "  make urls               - Show all service URLs"
	@echo "  make health             - Check service health"
	@echo "  make stack-up           - Start full stack"
	@echo "  make stack-down         - Stop full stack"

