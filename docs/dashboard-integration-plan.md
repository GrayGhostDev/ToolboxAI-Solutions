# Dashboard ↔ Backend Integration Plan

## Goals
- Ensure the Vercel-hosted dashboard forwards all API traffic to the Render backend with correct headers.
- Keep Render services (API, Redis, background workers) configured with the same environment assumptions that the dashboard expects.
- Provide CLI-driven health checks for both cloud deployments and the Docker development stack so regressions are caught quickly.

## 1. Vercel ↔ Backend Configuration
1. Confirm rewrites and headers
   - `cat apps/dashboard/vercel.json` (monorepo deploy) or `cat vercel.json` (root) to verify `/api/:path*` rewrites to `$VITE_API_BASE_URL`.
   - Grep for cached configs: `rg -n "VITE_API_BASE_URL" -g"*.json"`.
2. Sync environment variables
   - Pull current env for local testing: `vercel env pull --environment=production apps/dashboard/.env.production`.
   - Required keys for production dashboard:
     | Key | Purpose | Value/Source |
     | --- | --- | --- |
     | `VITE_API_URL` / `VITE_API_BASE_URL` | REST + GraphQL base | `https://toolboxai-backend-8j12.onrender.com` |
     | `VITE_PUSHER_KEY` / `VITE_PUSHER_CLUSTER` | realtime | Render secrets / Pusher dashboard |
     | `VITE_ENABLE_CLERK_AUTH` & `VITE_CLERK_PUBLISHABLE_KEY` | auth toggle | Render env group `toolboxai-frontend-env` |
     | `VITE_ENVIRONMENT`, `NODE_ENV` | runtime flags | `production` |
3. Validate headers after deploy
   - `vercel deploy --prebuilt` (if build already run via CI).
   - `curl -I https://toolboxai-dashboard.vercel.app/api/health` should now show:
     - `Access-Control-Allow-Origin: https://toolboxai-dashboard.vercel.app`
     - `Access-Control-Allow-Credentials: true`.
   - For preview deployments, temporarily override the header via Vercel dashboard (Project → Settings → Headers) or run `vercel env add VERCEL_PREVIEW_HOST <url>` and script a post-deploy hook to patch the header.

## 2. Render Services & Environment
1. Check service health
   - List services: `render services list | grep toolboxai`.
   - Inspect backend logs: `render logs toolboxai-backend --tail 200`.
   - Verify Redis add-on: `render redis list`.
2. Validate backend env groups
   - `render env-vars list toolboxai-backend | grep -E "ALLOWED_ORIGINS|TRUSTED_HOSTS|SUPABASE"`.
   - Ensure `ALLOWED_ORIGINS` includes `https://toolboxai-dashboard.vercel.app` (and any custom domains) and remove unusable wildcards like `https://*.vercel.app` if the backend framework rejects them.
   - Map frontend env group: `render env-groups list` then `render env-groups info toolboxai-frontend-env` to confirm `VITE_*` keys match Vercel.
3. Deploy sequencing
   - Always deploy backend first: `render deploy toolboxai-backend`.
   - After successful health checks, trigger Vercel deployment (`vercel deploy`) so the dashboard picks up any API schema changes.

## 3. Runtime Health Checks
Use these CLI checks each time backend or dashboard config changes:

```bash
# REST health
curl -s https://toolboxai-backend-8j12.onrender.com/api/health | jq

# GraphQL introspection from dashboard workspace
cd apps/dashboard
pnpm graphql:introspect

# WebSocket / realtime handshake
curl -I https://toolboxai-dashboard.vercel.app/api/pusher/health

# Config validator inside dashboard (dev only)
VITE_ENABLE_CONFIG_VALIDATION=true pnpm dev
```

If any check fails, inspect FastAPI logs (`render logs toolboxai-backend`) and confirm the Vercel rewrite is still pointing at the Render hostname.

## 4. Docker Development Mesh
1. Start full stack (frontend + backend + workers):
   ```bash
   cd infrastructure/docker/compose
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend dashboard postgres redis celery-worker celery-beat mcp-server agent-coordinator -d
   ```
2. Verify containers:
   ```bash
   docker compose ps
   docker compose logs backend | tail -n 50
   docker compose logs dashboard | tail -n 50
   ```
3. Exercises to mirror production traffic:
   - REST: `curl http://localhost:5179/api/health` (proxied through the dashboard container).
   - GraphQL: `curl -H 'Content-Type: application/json' -d '{"query":"{ __typename }"}' http://localhost:8009/graphql`.
   - Celery queue: `docker compose exec backend poetry run python scripts/queue_health.py` (script assumes existing helper; replace if necessary).
4. Tear down when finished: `docker compose down -v`.

## 5. Monitoring & Alerts
- Ensure `SENTRY_DSN_BACKEND`, `VITE_SENTRY_DSN`, and `toolboxai-monitoring` env group secrets are filled before going live.
- Hook Render deploy webhooks into the Vercel project so a backend deployment automatically triggers a dashboard redeploy: `vercel deploy --meta renderCommit=$RENDER_GIT_COMMIT`.
- Keep `pnpm test`, `pnpm lint`, and `pnpm graphql:introspect` in CI to catch schema drift before deployment.

Following the steps above keeps the Vercel dashboard, Render backend, and Docker-based local stack aligned so that API, realtime, and background services stay in sync.
