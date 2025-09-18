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

