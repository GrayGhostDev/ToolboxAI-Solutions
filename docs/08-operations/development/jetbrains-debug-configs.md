# JetBrains Debug Configurations (IntelliJ IDEA 2025.2)

> Reference: [JetBrains Debugging Guide](https://www.jetbrains.com/help/idea/2025.2/debugging-code.html?procedures.debugging&keymap=VSCode+%28macOS%29) — VS Code (macOS) keymap. Start/Continue = `F5`, Stop = `⇧F5`, Toggle Breakpoint = `F9`, Step Over = `F10`, Step Into = `F11`, Step Out = `⇧F11`.

## Project Topology

- **Frontend**: `apps/dashboard` (Vite + React 19, pnpm workspace, port **5179**).
- **Backend API**: `apps/backend/main.py` (FastAPI on uvicorn, port **8009**, Prometheus on `/metrics`).
- **GraphQL**: Mounted at `/graphql` via Ariadne (FastAPI process).
- **Async Workloads**: Celery (`apps/backend/workers/celery_app.py`) with worker, beat, and Flower (ports **5555** etc.).
- **Tests**: Vitest, Playwright, and Pytest. Shared TypeScript/GraphQL assets live under `packages/` and `schema/`.

## Prerequisites

1. **Tooling**
   - IntelliJ IDEA/WebStorm 2025.2 (or Fleet) with the VS Code keymap enabled.
   - Node.js ≥ 22 and pnpm ≥ 9 (`corepack enable`).
   - Python 3.12+ virtualenv in the repo root at `venv/` (NOT `.venv`).
   - Redis + PostgreSQL for Celery (use `docker compose -f infrastructure/docker/compose/docker-compose.dev.yml up redis postgres` as needed).
2. **Dependencies**
   ```bash
   pnpm install
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements-dev.txt
   pnpm run test:e2e:install   # installs Playwright browsers
   ```
3. **Environment files**
   - Copy `.env.example → .env`, `.env.local.example → .env.local`, `apps/dashboard/.env.example → apps/dashboard/.env.local`.
   - Populate Supabase, Clerk, OpenAI, Redis, and JWT secrets for local runs.
4. **JetBrains project setup**
   - Trust the repo, then set the Python SDK to `venv/`.
   - In *File ▸ Settings ▸ Languages & Frameworks ▸ JavaScript*, set package manager to **pnpm** and the Node interpreter to the system Node 22 install.
   - Mark `apps/backend` and `packages/shared-settings/ts` as Source Roots (if IDEA prompts).
   - Enable *Settings ▸ Build, Execution, Deployment ▸ Python Debugger ▸ Attach to subprocess automatically* so breakpoints hit inside uvicorn reload workers and Celery child processes.
   - Install the **EnvFile** plugin (optional) to load `.env` files directly into run configurations.

## Shared Environment Variables

| Variable | Source | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `.env` | Local Postgres (Render/Supabase connection string acceptable too). |
| `REDIS_URL` / `CELERY_BROKER_URL` | `.env` | Worker + cache connectivity. |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | `.env` | Required for auth + storage. |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | `.env` | Required for AI tasks; Celery workers expect them. |
| `JWT_SECRET_KEY`, `SECRET_KEY` | `.env` | Needed for FastAPI auth middleware. |
| `VITE_API_URL`, `VITE_SUPABASE_*`, `VITE_PUSHER_*` | `apps/dashboard/.env.local` | Keep frontend/bff parity. |
| `PLAYWRIGHT_BASE_URL` | `config/testing/playwright.config.ts` | Override base URL when debugging E2E. |

## Run/Debug Configuration Matrix

| Name | Type | Command / Target | Port(s) | When to use |
| --- | --- | --- | --- | --- |
| **FastAPI API (apps/backend)** | Python (module) | `uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload` | 8009 /metrics | REST + GraphQL debugging, Prometheus probe. |
| **Celery Worker (solo)** | Python (script) | `celery -A apps.backend.workers.celery_app worker --loglevel=info --pool=solo --queues=default,high_priority,email` | Redis 6379 | Breakpoints in tasks, retries, tenant context. |
| **Celery Beat** | Python (script) | `celery -A apps.backend.workers.celery_app beat --loglevel=info` | — | Cron-like schedule debugging. |
| **Celery Flower** | Python (script) | `celery -A apps.backend.workers.celery_app flower --port 5555` | 5555 | Inspect queues while stepping through workers. |
| **Dashboard – Vite Dev** | npm (pnpm) | `pnpm run dev` (package json in `apps/dashboard`) | 5179 | React UI dev server with Node inspector. |
| **Dashboard – JavaScript Debug** | JavaScript Debug | URL `http://localhost:5179` | Chrome DevTools | Attach to Chromium to hit TS breakpoints. |
| **Dashboard – Storybook** | npm (pnpm) | `pnpm run storybook` | 6006 | Component-level debugging. |
| **Dashboard – Vitest Watch** | npm (pnpm) | `pnpm run test:watch` | — | Unit tests with inspector attached. |
| **E2E – Playwright UI** | npm (pnpm) | `pnpm run test:e2e:ui` | 5179 (baseURL) | Visual test debugging with inspector. |
| **Backend – Pytest** | Python (pytest) | Target `tests/unit`, `tests/integration` | — | API/unit debugging. |
| **GraphQL Codegen Watch** | npm (pnpm) | `pnpm run codegen:watch` | — | Keeps TS typings current when editing schema/resolvers. |
| **Compound: Full Stack Dev** | Compound | `FastAPI API` + `Dashboard – Vite Dev` | 8009 / 5179 | One-click start for REST + UI. |
| **Compound: Background Workers** | Compound | `Celery Worker` + `Celery Beat` (+ optional Flower) | 5555 | Task + schedule debugging as a set. |

## Configuration Recipes

Follow the common pattern: *Run ▸ Edit Configurations ▸ ⊕ ▸ {type}*. All paths are relative to `$PROJECT_DIR$` (repo root).

### 1. FastAPI API (Python / uvicorn)

1. Add **Python** configuration.
2. Set **Module name** to `uvicorn` and **Parameters** to `apps.backend.main:app --host 127.0.0.1 --port 8009 --reload`.
3. Working directory: `$PROJECT_DIR$`. Enable *Emulate terminal in output console* for colored logs.
4. Environment variables (merge with your secrets):
   ```text
   ENVIRONMENT=development
   DEBUG=true
   PYTHONPATH=$PROJECT_DIR$
   PYTHONUNBUFFERED=1
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://localhost:6379/0
   SUPABASE_URL=...
   SUPABASE_ANON_KEY=...
   JWT_SECRET_KEY=...
   ```
5. Optional: add `.env` via EnvFile plugin instead of duplicating values.
6. Use `F9` to toggle breakpoints within routers, services, and dependency overrides; press `F5` to start debugging.
7. For hot reloads, JetBrains 2025.2 auto-attaches to the uvicorn subprocess when *Attach to subprocess automatically* is enabled. If a breakpoint does not hit after a reload, use *Run ▸ Attach to Process…* and select the spawned `uvicorn` PID.
8. Validate: `curl http://127.0.0.1:8009/health` and `curl http://127.0.0.1:8009/graphql` while the debugger is running.

### 2. Celery Worker (solo pool)

1. Add **Python** configuration named `Celery Worker (solo)`.
2. Set **Script path** to the `celery` executable inside `venv/bin/celery` (use the `…` picker) or set **Module name** to `celery`.
3. **Parameters**: `-A apps.backend.workers.celery_app worker --loglevel=info --pool=solo --concurrency=1 --queues=default,high_priority,email`.
4. Working directory: `$PROJECT_DIR$`. Environment variables should include broker/backend URLs and any API keys your tasks require.
5. Why `--pool=solo`: it forces a single-threaded worker so JetBrains can halt the process on breakpoints (multiprocessing pools spawn child processes that bypass the debugger).
6. Start Redis/Postgres locally or via Docker before launching. When running, Flower (if enabled) shows the worker at `127.0.0.1`.
7. Use the JetBrains *Frames* panel to inspect coroutine stacks; use *Evaluate Expression* to inspect tenant context (`self.tenant_context`).

### 3. Celery Beat

1. Duplicate the worker configuration and rename it `Celery Beat`.
2. Change **Parameters** to `-A apps.backend.workers.celery_app beat --loglevel=info`.
3. Keep the same env vars. Beat logs show which schedule entry fired; you can set breakpoints inside `apps/backend/tasks/...` functions invoked by beat ticks.

### 4. Celery Flower

1. Add a Python configuration with **Parameters** `-A apps.backend.workers.celery_app flower --port=5555 --basic-auth=admin:admin` (adjust auth as desired).
2. Open `http://localhost:5555` to view task states while breakpoints are active.

### 5. Dashboard – Vite Dev Server

1. Add an **npm** configuration (factory **npm**) and select `apps/dashboard/package.json`.
2. Command: `run`, Script: `dev`, Package manager: `pnpm`, Node interpreter: `project`.
3. Working directory: `apps/dashboard`.
4. Environment overrides (JetBrains lets you paste multiline values):
   ```text
   NODE_OPTIONS=--enable-source-maps --inspect=9229
   VITE_API_URL=http://127.0.0.1:8009
   VITE_ENV=development
   VITE_SUPABASE_URL=...
   VITE_SUPABASE_ANON_KEY=...
   VITE_PUSHER_KEY=...
   ```
5. Start the config (`F5`); the Vite server listens on `http://localhost:5179` (configured in `vite.config.js`). JetBrains automatically attaches the Node inspector thanks to `NODE_OPTIONS`.
6. Use *View ▸ Tool Windows ▸ Debug* to inspect server-side console logs and apply Live Edit tweaks.

### 6. Dashboard – JavaScript Debug (Chrome)

1. Add **JavaScript Debug** configuration with URL `http://localhost:5179`.
2. Precondition: the Vite dev server must already be running.
3. Press `F5` to open a Chrome instance with the JetBrains debugger extension; breakpoints in `.tsx` files resolve via source maps.
4. Use *Smart Step Into* (`⌥F11` in the VS Code keymap) to hop between async React components, as documented in the JetBrains guide.

### 7. Dashboard – Storybook

1. npm config targeting `apps/dashboard/package.json`, script `storybook`.
2. Optional env: `NODE_OPTIONS=--inspect=9330`.
3. Storybook runs at `http://localhost:6006`; pair with another JavaScript Debug config if you need to hit breakpoints in isolated stories.

### 8. Dashboard – Vitest Watch

1. npm config (`apps/dashboard`) with script `test:watch`.
2. Add `NODE_OPTIONS=--inspect-brk=9230` so JetBrains pauses before tests execute.
3. When the debugger breaks on the first test, press `F5` to continue; the IDE shows failing assertions inline with sourcemaps.

### 9. Playwright UI Runner

1. npm config (`apps/dashboard`) with script `test:e2e:ui`.
2. Env vars:
   ```text
   PLAYWRIGHT_BASE_URL=http://localhost:5179
   PWDEBUG=console
   ```
3. JetBrains opens the Playwright UI inspector; you can pause on `page.pause()` calls or add breakpoints inside test files.

### 10. Backend – Pytest

1. Add **Pytest** configuration.
2. Target: `tests/unit` (set *Additional Arguments* to `-ra -q` to match `pyproject.toml`).
3. Env vars: reuse the API config environment block so database connections resolve. Enable *Run with Python console* for interactive evaluation.

### 11. GraphQL Codegen Watch

1. npm config (`apps/dashboard`) with script `codegen:watch` (runs `graphql-codegen --watch`).
2. Keep this running whenever you edit `.graphql` schema files or backend resolvers so TypeScript types stay synchronized.

## Compound Configurations

1. Create **Compound** configuration `Full Stack Dev` and add:
   - `FastAPI API (apps/backend)`
   - `Dashboard – Vite Dev`
2. Optional *Activation*: set *Activate tool window* so both consoles open when pressing `F5`.
3. Create another **Compound** `Background Workers` with:
   - `Celery Worker (solo)`
   - `Celery Beat`
   - `Celery Flower` (optional)
4. Compounds honor breakpoints in each child configuration and keep logs grouped, matching JetBrains’ “Run several configurations at once” workflow from the documentation.

## Debugging Tips (JetBrains 2025.2)

- Use **Run ▸ Debugging Actions ▸ Evaluate Expression** to inspect live FastAPI/Celery state (`⇧⌘D` in the VS Code macOS keymap).
- Enable **Async Stack Traces** (Python) and **Show Async Frames** (JS) to follow coroutine chains through FastAPI dependencies and React Suspense boundaries.
- When uvicorn reloads due to file changes, JetBrains will briefly lose the connection; use **Rerun (⇧⌘F5)** rather than manual stop/start to preserve breakpoints.
- To debug HTTP traffic from inside the IDE, use the built-in **HTTP Client** (`.http` scratch files) while the debugger is paused; cookies/sessions reuse the running server instance.
- For Celery tasks that spawn additional processes, enable *PyCharm ▸ Preferences ▸ Build, Execution, Deployment ▸ Python Debugger ▸ Gevent compatible* if you rely on gevent-based pools.
- On the frontend, pair the JavaScript Debug config with Chrome DevTools' React Developer Tools for component tree inspection; JetBrains mirrors DOM breakpoints set in Chrome.

## Validation Checklist

1. **API**: Hit `http://127.0.0.1:8009/health` and `http://127.0.0.1:8009/graphql` with the debugger running; confirm breakpoints fire inside routers/resolvers.
2. **Dashboard**: Load `http://localhost:5179` via the JavaScript Debug config; toggle a breakpoint in `src/pages/AgentDashboard.tsx` (or any React page) and make sure it pauses.
3. **Celery**: Trigger a task (`curl -X POST http://127.0.0.1:8009/api/v1/tasks/submit` with sample data) and verify the worker hits breakpoints.
4. **Tests**: Run Pytest/Vitest/Playwright configs in Debug mode and inspect watch expressions.
5. **Storybook**: Open `http://localhost:6006`, interact with a story that calls the API proxy, and verify logs appear in the Vite server console.

## Troubleshooting

- **Port already in use**: run `lsof -ti:8009,5179,5555 | xargs kill -9` before restarting debugging sessions.
- **Breakpoints skipped in uvicorn**: disable `--reload` temporarily or enable “Attach to subprocess automatically” so the debugger follows the reloader child.
- **Celery tasks never hit breakpoints**: confirm you are using `--pool=solo` (or set *Run ▸ Debugging Actions ▸ Attach to Process* on the spawned worker PID).
- **Playwright cannot find Chrome**: rerun `pnpm run test:e2e:install` and ensure `PLAYWRIGHT_BROWSERS_PATH=0` isn’t set.
- **Environment drift**: prefer referencing `.env` files (EnvFile plugin) instead of duplicating secrets across configs; update the `.env.example` files if you add new required keys.

Document owners: Platform Engineering. Update whenever ports, scripts, or run targets change.
