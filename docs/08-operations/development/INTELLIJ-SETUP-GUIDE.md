# IntelliJ IDEA Complete Setup Guide for ToolBoxAI-Solutions

**Last Updated:** November 13, 2025
**IntelliJ IDEA Version:** 2025.2
**Target Platform:** macOS (adaptable to other platforms)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Project Setup](#initial-project-setup)
3. [Python SDK Configuration](#python-sdk-configuration)
4. [Node.js & pnpm Configuration](#nodejs--pnpm-configuration)
5. [Environment Files Setup](#environment-files-setup)
6. [Installing Required Plugins](#installing-required-plugins)
7. [Creating Run/Debug Configurations](#creating-rundebug-configurations)
8. [Keyboard Shortcuts (VS Code Keymap)](#keyboard-shortcuts-vs-code-keymap)
9. [Testing Your Setup](#testing-your-setup)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

```bash
# Verify versions
node --version        # Should be v22.x or higher
pnpm --version        # Should be 9.15.0 or higher
python3 --version     # Should be 3.12.x or higher
docker --version      # Should be 25.x or higher
redis-cli --version   # Redis 7.x
psql --version        # PostgreSQL 16.x
```

### Download Links

- **IntelliJ IDEA Ultimate 2025.2**: [Download](https://www.jetbrains.com/idea/download/)
- **Node.js 22 LTS**: [Download](https://nodejs.org/)
- **Docker Desktop**: [Download](https://www.docker.com/products/docker-desktop/)
- **PostgreSQL 16**: [Download](https://www.postgresql.org/download/)
- **Redis 7**: [Download](https://redis.io/download/) or use Docker

---

## Initial Project Setup

### Step 1: Open the Project

1. Launch IntelliJ IDEA 2025.2
2. **File → Open** and navigate to:
   ```
   /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions
   ```
3. Click **Open**
4. When prompted "Trust and Open Project?", click **Trust Project**

### Step 2: Enable VS Code Keymap (Optional but Recommended)

1. Go to **File → Settings** (or **IntelliJ IDEA → Settings** on macOS)
2. Navigate to **Keymap**
3. From the dropdown, select **VS Code (macOS)** if you're on macOS, or **VS Code** for other platforms
4. Click **OK**

**Key Shortcuts:**
- `F5` - Start/Continue Debugging
- `⇧F5` - Stop Debugging
- `F9` - Toggle Breakpoint
- `F10` - Step Over
- `F11` - Step Into
- `⇧F11` - Step Out

---

## Python SDK Configuration

### Step 1: Create Virtual Environment

Open the terminal in IntelliJ IDEA:

```bash
# Navigate to project root
cd /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions

# Create virtual environment (MUST be named 'venv/')
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**⚠️ IMPORTANT:** The virtual environment MUST be named `venv/` (NOT `.venv` or `venv_clean`)

### Step 2: Configure Python Interpreter in IntelliJ

1. Go to **File → Project Structure** (`⌘;` on macOS)
2. Select **SDKs** under **Platform Settings**
3. Click the **+** button and select **Add Python SDK**
4. Choose **Virtualenv Environment**
5. Select **Existing environment**
6. Set the interpreter path to:
   ```
   /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/venv/bin/python
   ```
7. Click **OK**

### Step 3: Set Project SDK

1. Still in **Project Structure**, go to **Project** (under **Project Settings**)
2. Set the **SDK** dropdown to the `venv` Python interpreter you just configured
3. Set **Language level** to **Python 3.12**
4. Click **Apply** then **OK**

### Step 4: Mark Source Roots

1. In the **Project** view (left sidebar), right-click on `apps/backend`
2. Select **Mark Directory as → Sources Root**
3. Repeat for `packages/shared-settings/ts` if it exists

### Step 5: Configure Python Debugger

1. Go to **File → Settings → Build, Execution, Deployment → Python Debugger**
2. Enable **"Attach to subprocess automatically"**
   - This ensures breakpoints work inside uvicorn reload workers and Celery child processes
3. Click **OK**

---

## Node.js & pnpm Configuration

### Step 1: Configure Node.js

1. Go to **File → Settings → Languages & Frameworks → Node.js**
2. Set the **Node interpreter** to your system Node 22 installation (usually `/usr/local/bin/node` or use the `...` button to find it)
3. Click **OK**

### Step 2: Configure Package Manager (pnpm)

1. In the same settings area, go to **Languages & Frameworks → Node.js and NPM**
2. Click on the **Package manager** dropdown and select **pnpm**
3. Verify the pnpm path (usually `/usr/local/bin/pnpm`)
4. Click **OK**

### Step 3: Install Frontend Dependencies

Open the terminal in IntelliJ IDEA:

```bash
# Install all pnpm workspaces
pnpm install

# Install Playwright browsers for E2E testing
pnpm run test:e2e:install
```

---

## Environment Files Setup

### Step 1: Copy Environment Templates

```bash
# Backend environment
cp .env.example .env
cp .env.local.example .env.local

# Frontend environment
cp apps/dashboard/.env.example apps/dashboard/.env.local
```

### Step 2: Configure .env Files

Edit `.env` with your actual credentials:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/toolboxai_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# AI Services
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Authentication
JWT_SECRET_KEY=your_jwt_secret_here
SECRET_KEY=your_secret_key_here

# Clerk (OAuth)
CLERK_SECRET_KEY=sk_test_...
```

Edit `apps/dashboard/.env.local`:

```bash
VITE_API_URL=http://127.0.0.1:8009
VITE_ENV=development
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_PUSHER_KEY=your_pusher_key_here
VITE_PUSHER_CLUSTER=mt1
```

**Security Note:** Never commit `.env` or `.env.local` files! Only commit `.example` files.

### Step 3: Start Required Services

```bash
# Start PostgreSQL and Redis via Docker
docker compose -f infrastructure/docker/compose/docker-compose.dev.yml up -d redis postgres

# Verify they're running
docker ps
redis-cli ping  # Should return "PONG"
psql -U postgres -c "SELECT version();"  # Should show PostgreSQL version
```

---

## Installing Required Plugins

### Step 1: Open Plugin Marketplace

1. Go to **File → Settings → Plugins**
2. Click on the **Marketplace** tab

### Step 2: Install Essential Plugins

Search for and install the following:

#### Required Plugins:
1. **EnvFile** - Load environment variables from `.env` files
2. **Python** - Should be pre-installed with Ultimate edition
3. **JavaScript Debugger** - Should be pre-installed

#### Recommended Plugins:
4. **Docker** - Docker integration (pre-installed with Ultimate)
5. **GraphQL** - GraphQL schema and query support
6. **Tailwind CSS** - If using Tailwind
7. **.ignore** - .gitignore support
8. **Rainbow Brackets** - Visual bracket matching

### Step 3: Restart IntelliJ IDEA

After installing plugins, restart the IDE.

---

## Creating Run/Debug Configurations

### Configuration Overview

We'll create the following configurations:

1. **FastAPI Backend** (uvicorn)
2. **Dashboard Vite Dev Server** (React)
3. **Celery Worker** (async tasks)
4. **Celery Beat** (scheduled tasks)
5. **Celery Flower** (monitoring)
6. **Dashboard JavaScript Debug** (Chrome)
7. **Backend Pytest** (tests)
8. **Dashboard Vitest** (tests)
9. **Playwright E2E Tests**
10. **Compound: Full Stack Dev** (Backend + Frontend together)
11. **Compound: Background Workers** (Celery Worker + Beat + Flower)

---

### Configuration 1: FastAPI Backend

**Create the configuration:**

1. Click **Run → Edit Configurations** (top toolbar)
2. Click the **+** button → **Python**
3. Name: `FastAPI Backend (Port 8009)`

**Configure:**

- **Module name**: `uvicorn` (NOT Script path)
- **Parameters**:
  ```
  apps.backend.main:app --host 127.0.0.1 --port 8009 --reload
  ```
- **Working directory**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions
  ```
  (Use `$PROJECT_DIR$` macro)
- **Environment variables**: Click the folder icon and add:
  ```
  ENVIRONMENT=development
  DEBUG=true
  PYTHONPATH=$PROJECT_DIR$
  PYTHONUNBUFFERED=1
  ```

  **Option 1: Using EnvFile Plugin (Recommended)**
  - Click the **EnvFile** tab
  - Click **+** and add `.env`
  - Click **+** and add `.env.local`

  **Option 2: Manual Entry**
  - Paste your entire `.env` file contents

- **Python interpreter**: Select the `venv` interpreter
- **Options**:
  - ✅ Enable "Emulate terminal in output console"
  - ✅ Enable "Run with Python Console" (optional, for debugging)

**Click OK to save.**

---

### Configuration 2: Dashboard Vite Dev Server

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **npm**
3. Name: `Dashboard - Vite Dev (Port 5179)`

**Configure:**

- **Package.json**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json
  ```
- **Command**: `run`
- **Scripts**: `dev`
- **Package manager**: `pnpm`
- **Node interpreter**: Use the system Node 22 interpreter
- **Working directory**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/apps/dashboard
  ```
- **Environment variables**:
  ```
  NODE_OPTIONS=--enable-source-maps --inspect=9229
  VITE_API_URL=http://127.0.0.1:8009
  VITE_ENV=development
  ```

  **Or load from** `apps/dashboard/.env.local` using EnvFile plugin

**Click OK to save.**

---

### Configuration 3: Celery Worker (Solo Pool)

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **Python**
3. Name: `Celery Worker (Solo)`

**Configure:**

- **Module name**: `celery`
- **Parameters**:
  ```
  -A apps.backend.workers.celery_app worker --loglevel=info --pool=solo --concurrency=1 --queues=default,high_priority,email
  ```
- **Working directory**: `$PROJECT_DIR$`
- **Environment variables**: Same as FastAPI Backend (load from `.env`)
- **Python interpreter**: Select the `venv` interpreter

**Why `--pool=solo`?**
Solo pool forces single-threaded execution, allowing IntelliJ to hit breakpoints. Multiprocessing pools spawn child processes that bypass the debugger.

**Click OK to save.**

---

### Configuration 4: Celery Beat

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **Python**
3. Name: `Celery Beat`

**Configure:**

- **Module name**: `celery`
- **Parameters**:
  ```
  -A apps.backend.workers.celery_app beat --loglevel=info
  ```
- **Working directory**: `$PROJECT_DIR$`
- **Environment variables**: Same as FastAPI Backend (load from `.env`)
- **Python interpreter**: Select the `venv` interpreter

**Click OK to save.**

---

### Configuration 5: Celery Flower (Monitoring)

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **Python**
3. Name: `Celery Flower (Port 5555)`

**Configure:**

- **Module name**: `celery`
- **Parameters**:
  ```
  -A apps.backend.workers.celery_app flower --port=5555 --basic-auth=admin:admin
  ```
- **Working directory**: `$PROJECT_DIR$`
- **Environment variables**: Same as FastAPI Backend (load from `.env`)
- **Python interpreter**: Select the `venv` interpreter

**Access Flower at:** `http://localhost:5555` (username: `admin`, password: `admin`)

**Click OK to save.**

---

### Configuration 6: Dashboard - JavaScript Debug (Chrome)

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **JavaScript Debug**
3. Name: `Dashboard - Chrome Debug`

**Configure:**

- **URL**: `http://localhost:5179`
- **Browser**: Chrome (or Chromium)

**Prerequisites:**
- The **Dashboard - Vite Dev** server must be running first
- Start that configuration, then start this one

**Usage:**
- Set breakpoints in `.tsx` files in `apps/dashboard/src/`
- Press `F5` to start debugging
- IntelliJ opens Chrome with debugger attached
- Breakpoints resolve via source maps

**Click OK to save.**

---

### Configuration 7: Backend - Pytest

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **pytest**
3. Name: `Backend - Pytest (All Tests)`

**Configure:**

- **Target**: Choose "Custom" and set path to:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/tests
  ```
- **Additional Arguments**:
  ```
  -ra -q --tb=short
  ```
- **Working directory**: `$PROJECT_DIR$`
- **Environment variables**: Same as FastAPI Backend (load from `.env`)
- **Python interpreter**: Select the `venv` interpreter
- **Options**:
  - ✅ Enable "Run with Python Console"

**To run only unit tests:**
- Create another configuration named `Backend - Pytest (Unit Only)`
- Set **Additional Arguments** to: `-m unit -ra -q`

**To run only integration tests:**
- Create another configuration named `Backend - Pytest (Integration Only)`
- Set **Additional Arguments** to: `-m integration -ra -q`

**Click OK to save.**

---

### Configuration 8: Dashboard - Vitest

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **npm**
3. Name: `Dashboard - Vitest Watch`

**Configure:**

- **Package.json**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json
  ```
- **Command**: `run`
- **Scripts**: `test:watch`
- **Package manager**: `pnpm`
- **Node interpreter**: System Node 22
- **Working directory**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/apps/dashboard
  ```
- **Environment variables**:
  ```
  NODE_OPTIONS=--inspect-brk=9230
  ```

**Usage:**
- Vitest runs in watch mode
- Set breakpoints in test files
- IntelliJ pauses before first test executes
- Press `F5` to continue

**Click OK to save.**

---

### Configuration 9: Playwright E2E Tests

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **npm**
3. Name: `E2E - Playwright UI`

**Configure:**

- **Package.json**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/package.json
  ```
- **Command**: `run`
- **Scripts**: `test:e2e:ui`
- **Package manager**: `pnpm`
- **Node interpreter**: System Node 22
- **Working directory**:
  ```
  /Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/apps/dashboard
  ```
- **Environment variables**:
  ```
  PLAYWRIGHT_BASE_URL=http://localhost:5179
  PWDEBUG=console
  ```

**Prerequisites:**
- Both **FastAPI Backend** and **Dashboard - Vite Dev** must be running

**Usage:**
- Opens Playwright UI inspector
- Can pause on `page.pause()` calls
- Can add breakpoints in test files

**Click OK to save.**

---

### Configuration 10: Compound - Full Stack Dev

This compound configuration starts both backend and frontend together.

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **Compound**
3. Name: `🚀 Full Stack Dev`

**Configure:**

- Click **+** to add configurations:
  1. Add **FastAPI Backend (Port 8009)**
  2. Add **Dashboard - Vite Dev (Port 5179)**
- **Store as project file**: ✅ Enabled (so it's shared via git)
- **Options**:
  - ✅ Activate tool window (opens both consoles)

**Usage:**
- Click this configuration and press `F5`
- Both backend and frontend start together
- Both consoles appear in tabs
- Breakpoints work in both services

**Click OK to save.**

---

### Configuration 11: Compound - Background Workers

This compound configuration starts Celery worker, beat, and Flower together.

**Create the configuration:**

1. Click **Run → Edit Configurations**
2. Click the **+** button → **Compound**
3. Name: `⚙️ Background Workers`

**Configure:**

- Click **+** to add configurations:
  1. Add **Celery Worker (Solo)**
  2. Add **Celery Beat**
  3. Add **Celery Flower (Port 5555)** (optional)
- **Store as project file**: ✅ Enabled
- **Options**:
  - ✅ Activate tool window

**Usage:**
- Starts all background task processing
- Use Flower to monitor tasks at `http://localhost:5555`
- Breakpoints work in task functions

**Click OK to save.**

---

## Keyboard Shortcuts (VS Code Keymap)

If you enabled the VS Code keymap, use these shortcuts:

### Debugging
- **`F5`** - Start/Continue Debugging
- **`⇧F5`** - Stop Debugging
- **`⇧⌘F5`** - Restart Debugging (rerun)
- **`F9`** - Toggle Breakpoint
- **`F10`** - Step Over
- **`F11`** - Step Into
- **`⇧F11`** - Step Out
- **`⌥F11`** - Smart Step Into (React async components)
- **`⇧⌘D`** - Evaluate Expression

### Navigation
- **`⌘P`** - Quick Open File
- **`⌘⇧P`** - Command Palette
- **`⌥←/→`** - Navigate Back/Forward
- **`⌘B`** - Go to Definition
- **`⌘⇧F`** - Find in Files

### Running
- **`⌃⇧R`** - Select configuration and run
- **`⌃⇧D`** - Select configuration and debug

---

## Testing Your Setup

### Test 1: FastAPI Backend

1. Select **FastAPI Backend (Port 8009)** from the run configurations dropdown
2. Press `F5` to start debugging
3. In `apps/backend/api/v1/health.py`, set a breakpoint on the return statement
4. Open browser to `http://127.0.0.1:8009/health`
5. Debugger should pause at your breakpoint
6. Press `F5` to continue
7. Verify response: `{"status": "ok"}`

**GraphQL Test:**
```bash
curl http://127.0.0.1:8009/graphql
```
Should return GraphQL playground HTML.

### Test 2: Dashboard Frontend

1. Select **Dashboard - Vite Dev (Port 5179)**
2. Press `F5` to start
3. Wait for "Local: http://localhost:5179" in console
4. Open browser to `http://localhost:5179`
5. Verify the dashboard loads

**With JavaScript Debug:**
1. Keep Vite dev server running
2. Select **Dashboard - Chrome Debug**
3. Press `F5`
4. Set a breakpoint in `apps/dashboard/src/App.tsx`
5. Reload the page
6. Debugger should pause at your breakpoint

### Test 3: Full Stack (Compound)

1. Select **🚀 Full Stack Dev**
2. Press `F5`
3. Both backend and frontend should start
4. Both consoles appear in tabs
5. Backend: `http://127.0.0.1:8009/health`
6. Frontend: `http://localhost:5179`

### Test 4: Celery Worker

1. Ensure Redis is running: `redis-cli ping` → PONG
2. Select **Celery Worker (Solo)**
3. Press `F5`
4. Console should show: `[tasks] Received task:`
5. In `apps/backend/tasks/example_task.py`, set a breakpoint
6. Trigger a task from the FastAPI endpoint
7. Debugger should pause in the task function

### Test 5: Pytest

1. Select **Backend - Pytest (All Tests)**
2. Press `F5`
3. Tests should run and show results
4. Set a breakpoint in a test file
5. Re-run in debug mode
6. Debugger should pause at your breakpoint

---

## Troubleshooting

### Issue: "Port 8009 already in use"

**Solution:**
```bash
# Find process using port
lsof -ti:8009

# Kill the process
lsof -ti:8009 | xargs kill -9

# Or kill multiple ports at once
lsof -ti:8009,5179,5555 | xargs kill -9
```

### Issue: "Module 'uvicorn' not found"

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify uvicorn is installed
pip show uvicorn
```

### Issue: Breakpoints not hitting in FastAPI

**Solution:**
1. Go to **File → Settings → Build, Execution, Deployment → Python Debugger**
2. Enable **"Attach to subprocess automatically"**
3. Restart the FastAPI configuration
4. Alternatively, disable `--reload` in the parameters (but this disables hot reload)

### Issue: Celery worker breakpoints not working

**Solution:**
- Verify you're using `--pool=solo` in the parameters
- Multi-process pools bypass the debugger
- Solo pool forces single-threaded execution

### Issue: "Cannot find package.json" for npm configs

**Solution:**
- Verify the path is absolute, not relative
- Use the `...` picker to browse to the file
- Ensure pnpm is selected as the package manager

### Issue: Environment variables not loading

**Solution:**

**Option 1: EnvFile Plugin**
1. Verify EnvFile plugin is installed
2. In the configuration, click the **EnvFile** tab
3. Add `.env` and `.env.local` files
4. Check **Enable EnvFile**

**Option 2: Manual Entry**
1. Copy the contents of `.env`
2. Paste into the **Environment variables** field
3. Format: `KEY=value` separated by semicolons or newlines

### Issue: "Redis connection refused"

**Solution:**
```bash
# Start Redis via Docker
docker compose -f infrastructure/docker/compose/docker-compose.dev.yml up -d redis

# Or start Redis locally (macOS)
brew services start redis

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

### Issue: "PostgreSQL connection refused"

**Solution:**
```bash
# Start PostgreSQL via Docker
docker compose -f infrastructure/docker/compose/docker-compose.dev.yml up -d postgres

# Or start PostgreSQL locally (macOS)
brew services start postgresql@16

# Verify PostgreSQL is running
psql -U postgres -c "SELECT version();"
```

### Issue: pnpm command not found

**Solution:**
```bash
# Enable corepack (recommended)
corepack enable

# Verify pnpm version
pnpm --version  # Should be 9.15.0+

# If not installed, install globally
npm install -g pnpm@9.15.0
```

### Issue: Python interpreter not showing `venv`

**Solution:**
1. Ensure the virtual environment was created correctly:
   ```bash
   ls -la venv/bin/python
   ```
2. In IntelliJ, go to **File → Project Structure → SDKs**
3. Click **+** → **Add Python SDK** → **Virtualenv Environment**
4. Select **Existing environment**
5. Browse to: `/Users/grayghostdata/Development/Clients/ToolBoxAI-Solutions/venv/bin/python`
6. Click **OK**

---

## Advanced Tips

### Tip 1: Use HTTP Client for API Testing

IntelliJ has a built-in HTTP Client:

1. Create a new file: `test-api.http`
2. Add requests:
   ```http
   ### Health Check
   GET http://127.0.0.1:8009/health

   ### GraphQL Query
   POST http://127.0.0.1:8009/graphql
   Content-Type: application/json

   {
     "query": "{ __typename }"
   }
   ```
3. Click the ▶️ icon next to each request to execute
4. Responses appear in a panel below

### Tip 2: Enable Async Stack Traces

For better debugging of async code:

1. **Python**: Go to **File → Settings → Build, Execution, Deployment → Python Debugger**
2. Enable **"Show return values"** and **"Gevent compatible"** (if using gevent)
3. **JavaScript**: In the Debug panel, click ⚙️ → Enable **"Show Async Frames"**

### Tip 3: Use Smart Step Into

When debugging React components:

1. Set a breakpoint in a component
2. When paused, press **`⌥F11`** (Smart Step Into)
3. IntelliJ shows a list of all function calls on that line
4. Select which function to step into

### Tip 4: Create a "Quick Test" Configuration

For rapid testing of a single file:

1. Right-click any test file
2. Select **Run 'pytest in <filename>'**
3. IntelliJ creates a temporary configuration
4. You can save it for reuse

### Tip 5: Use Live Edit for Frontend

When debugging the dashboard:

1. Start **Dashboard - Chrome Debug**
2. Make changes to a React component
3. Save the file
4. Changes appear immediately in Chrome (Vite HMR)
5. No need to reload or restart

---

## Exporting and Sharing Configurations

### Export All Configurations

1. Go to **Run → Edit Configurations**
2. For each configuration, enable **"Store as project file"**
3. Configurations are saved in `.idea/runConfigurations/`
4. Commit these files to git (if desired)

### Import Configurations

If configurations are stored in the repo:

1. Clone the repo
2. Open in IntelliJ IDEA
3. Configurations automatically appear in the dropdown

**Note:** Sensitive environment variables should NOT be committed. Use `.env` files instead.

---

## Summary Checklist

Before you start coding, ensure:

- ✅ IntelliJ IDEA 2025.2 installed
- ✅ Project opened and trusted
- ✅ Python 3.12+ virtual environment created at `venv/`
- ✅ Python SDK configured to `venv/bin/python`
- ✅ Node.js 22+ configured
- ✅ pnpm 9.15.0+ configured as package manager
- ✅ Dependencies installed: `pip install -r requirements.txt` and `pnpm install`
- ✅ Environment files configured: `.env`, `.env.local`, `apps/dashboard/.env.local`
- ✅ Redis and PostgreSQL running
- ✅ EnvFile plugin installed (optional but recommended)
- ✅ All 11 run/debug configurations created
- ✅ Tested: FastAPI backend, Dashboard frontend, Celery worker, Pytest

---

## Next Steps

Now that your IntelliJ IDEA is fully configured:

1. **Start Development**: Use **🚀 Full Stack Dev** to run both backend and frontend
2. **Run Tests**: Use the Pytest and Vitest configurations
3. **Debug Issues**: Set breakpoints and use `F5` to debug
4. **Monitor Tasks**: Use **⚙️ Background Workers** and Flower
5. **Read Documentation**: See `/docs/` for feature-specific guides

---

## Additional Resources

- **JetBrains Debugging Guide**: [Link](https://www.jetbrains.com/help/idea/2025.2/debugging-code.html)
- **ToolBoxAI Architecture**: `/docs/02-architecture/`
- **API Documentation**: `/docs/03-api/`
- **Deployment Guide**: `/docs/08-operations/deployment/`
- **Main CLAUDE.md**: `/CLAUDE.md`

---

**Setup completed!** 🎉

You're now ready to develop, debug, and test ToolBoxAI-Solutions with IntelliJ IDEA 2025.2.

**Questions or issues?** Check the [Troubleshooting](#troubleshooting) section or refer to the main documentation in `/docs/`.

---

*Document maintained by Platform Engineering*
*Last reviewed: November 13, 2025*
