# Root Asset Inventory

This inventory captures every top-level directory/file in the repository and assigns a domain owner plus canonical responsibility. Use it as the starting point whenever reorganizing or auditing the codebase.

| Path | Domain | Purpose / Notes |
| ---- | ------ | --------------- |
| `api/` | Backend Integrations | Legacy API adapters and service clients pending migration into `apps/backend`. |
| `apps/backend/` | Backend | FastAPI service, Celery workers, and shared backend packages. |
| `apps/dashboard/` | Frontend | React dashboard application (should remain code-only; docs/scripts live under `docs/` and `scripts/`). |
| `Archive/` | Historical | Frozen snapshots and audits retained for reference only. |
| `ArmorATD/` | Client Assets | External client deliverables (keep isolated). |
| `config/` | Configuration | Runtime configuration, env templates, and secrets wiring. |
| `core/` | AI Platform | Agent orchestration, MCP integrations, and shared AI logic. |
| `data/` | Data Ops | Datasets, ETL helpers, and analytical assets. |
| `database/` | DB Tooling | Schema definitions, migrations, and DB utilities. |
| `docs/` | Documentation | Canonical documentation tree (see `docs/10-meta/documentation/CANONICAL_PATHS.md`). |
| `images/` | Media | Shared project imagery (used by docs and marketing). |
| `infrastructure/` | Infrastructure | Docker, Kubernetes, Terraform, and deployment automation. |
| `logs/` | Operational | Persistent logs and monitoring artifacts (ignored in commits). |
| `middleware/` | Services | Cross-cutting middleware/libraries awaiting consolidation into apps. |
| `monitoring/` | Observability | Alerting/monitoring configs and dashboards. |
| `node_modules/` | Dependencies | Workspace-level packages (managed via npm workspaces). |
| `packages/` | Shared Packages | Reusable TypeScript/Node packages consumed by apps. |
| `public/` | Assets | Shared static assets (non-dashboard specific). |
| `roblox/` | Roblox Platform | Roblox integration code, plugins, and assets. |
| `schema/` | Schemas | JSON/YAML schema definitions consumed by services. |
| `scripts/` | Tooling | All automation, validation, and helper scripts (see `scripts/README.md`). |
| `services/` | Services | Additional microservices under development. |
| `src/` | Shared Source | Cross-application Python/TS sources that don’t belong exclusively to an app. |
| `supabase/` | Supabase | Supabase-specific migrations, functions, and configs. |
| `TeamCity/` | CI | TeamCity build configurations. |
| `tests/` | Tests | Top-level integration/regression tests. |
| `toolboxai_settings/` | Settings | Python settings package consumed across apps. |
| `uploads/` | Uploads | Temporary uploaded assets (excluded via .gitignore). |
| `worktree-tasks/` | Worktree | Scripts/docs for worktree automation. |
| `Makefile` | Tooling | Entry point for local automation targets. |
| `package.json` / `pyproject.toml` / `requirements.txt` | Build | Workspace manifests (Node + Python). |

> **Maintenance Rule:** if you add a new top-level item, update this file and the canonical documentation paths file in the same PR.

