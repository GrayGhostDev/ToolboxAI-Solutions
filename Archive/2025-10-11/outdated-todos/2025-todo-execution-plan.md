# 2025 Execution Plan to Close Remaining TODOs

Branch: chore/todos-2025-execution-plan-20251005
Catalog: docs/todos/todo-catalog.json (generated)
Scope period: October 2025

1) Overview and goals
- Aggregate and reconcile all TODO/FIXME items from:
  - Root TODO.md
  - docs/TODO.md
  - Code-level markers (TODO, FIXME)
- Create a single canonical catalog and a tracked execution plan.
- Implement remaining items in waves without changing any global variables or the existing filesystem layout.
- Maintain 2025 standards for security, testing, and performance.

2) Guardrails and constraints
- Do not rename, move, or delete any existing files/directories unless explicitly approved.
- Do not change or remove any globals, environment variable names, or top-level configuration keys.
- Additive-only: new docs/scripts/CI updates allowed when they don’t disrupt existing behavior.
- Performance: respect 16ms UI frame budget; background tasks <= 25% CPU; memory <= 2GB per session.
- Secrets: never committed in plaintext; use environment variables or secret managers.
- Shell: POSIX-compatible scripts.

3) Backlog summary (auto-updated via catalog)
- Source of truth: docs/todos/todo-catalog.json
- Use scripts/todo-scan.sh to regenerate the catalog.
- Suggested counts to track: totals by tag (TODO/FIXME), area (backend/frontend/infra/docs), severity, and estimated effort.

4) Work item template
- id: canonical id from the catalog (e.g., todo-000123)
- title: short, action-oriented
- description: current gap and intended change
- type: bugfix | refactor | docs | feature-parity | performance
- severity: critical | high | medium | low
- files: list all associated paths and line ranges
- acceptance_criteria:
  - [ ] Tests updated/added; thresholds met
  - [ ] Docs updated (CHANGELOG, feature docs)
  - [ ] No globals or structure changes
  - [ ] CI green (lint/tests/security/perf smoke)
- tests: unit | integration | e2e (as applicable)
- docs_updates: exact file paths to update
- risk_and_rollback: summary

5) Phased plan and scheduling
- Wave 0 (1–2 days): discovery and reconciliation
  - Generate catalog JSON and seed this plan with items and file associations.
  - Acceptance gate: valid catalog; plan doc committed; CI green.
- Wave 1 (2–4 days): quick wins and CI hardening
  - Minor docs/comment fixes, small refactors, non-breaking changes. Tighten CI gates.

  Phase 1 tracked issues:
  - [#37 feat(backend): complete storage upload and media endpoints](https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues/37)
  - [#38 feat(backend): implement multi-tenancy middleware + tenant endpoints and scripts](https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues/38)
  - [#39 feat(dashboard): finalize Pusher client, event hooks, and status UI](https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues/39)

  Milestone (temporary until Projects v2 is available):
  - Phase 1 Execution: https://github.com/GrayGhostDev/ToolboxAI-Solutions/milestone/1

- Wave 2 (3–7 days): correctness and missing endpoints/tests
  - Complete uploads/media endpoints, multi-tenancy middleware and endpoints.
  - Fill missing unit/integration tests.
- Wave 3 (5–10 days): performance and error handling
  - Replace generic exceptions, add structured errors, optimize N+1 queries, caching, pagination.
- Wave 4 (2–3 days): polish and cleanup
  - Remove obsolete TODOs, finalize docs, ensure catalog is empty or deferred with due dates.

6) RACI and review process
- Authors: implement items in small PRs with the template above.
- Reviewers: enforce guardrails; check tests/coverage, docs, and CI.
- Approvals: code owners where applicable.

7) Exit criteria
- docs/todos/todo-catalog.json has zero open items or only deferred ones with rationale and due dates.
- This plan is updated with final status and metrics.
- CI pipelines consistently green; coverage at or above targets.

Appendix A — Priority backlog (seed)
- File storage: finalize API endpoints for uploads and media (apps/backend/api/v1/endpoints/uploads.py, media.py)
- Multi-tenancy: middleware and endpoints (tenant_middleware.py; tenant_* endpoints; tenant scripts)
- Error handling: replace generic exceptions in worst offenders; add Sentry; docs
- Testing: raise coverage >= 80% repo-wide; add integration and e2e suites; factories
- Observability: wire Prometheus/Grafana/Jaeger dashboards and alerts
