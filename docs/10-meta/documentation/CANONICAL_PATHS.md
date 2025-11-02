# Canonical Documentation Paths

All Markdown documentation belongs under `docs/` according to the following canonical locations. Use this table to decide where new files live and to validate future cleanups.

| Category | Canonical Path | Notes |
| -------- | -------------- | ----- |
| Architecture & Overview | `docs/02-overview`, `docs/03-architecture` | Product, system, and architectural primers. |
| API Docs | `docs/04-api` | REST/OpenAPI specs, endpoint guides. |
| Implementation Guides | `docs/05-implementation` | Development setup, feature implementations, testing, deployment how-tos. |
| Feature Guides | `docs/06-features` | User-facing features and UI documentation. |
| User Guides | `docs/07-user-guides` | Role-specific guides. |
| Operations & Security | `docs/08-operations` | Maintenance, security, troubleshooting, cleanup plans. |
| Reference | `docs/09-reference` | Security policies, requirements, troubleshooting reference. |
| Meta / Process | `docs/10-meta` | Project process, changelog, workflows, AI guidance. |
| Reports & Status | `docs/11-reports` | All status reports, progress logs, audit outputs (use `docs/11-reports/dashboard` for dashboard-specific reports). |
| SDKs | `docs/12-sdks` | SDK docs and examples. |
| Phase 2+ deliverables | `docs/phase2` | Time-bound phase documentation. |
| Archives | `docs/Archive` | Frozen copies retained for legal/compliance reasons. |

**Rules**

1. **App directories stay code-only.** Any Markdown detected in `apps/**` should be relocated here (use `scripts/documentation/enforce-doc-locations.py`).
2. **Reports choose `docs/11-reports`.** Prefix subdirectories by domain (`dashboard/`, `backend/`, etc.).
3. **Testing docs live under `docs/05-implementation/testing`.** Split guides vs. reports accordingly.
4. **Design references go to `docs/05-implementation/design` or `docs/06-features/.../components`.**
5. **Link updates are mandatory.** When a file moves, run `scripts/documentation/update-link-references.py --old <old/path> --new <new/path>` and include results in the same commit.

Embedding these rules into CI is handled by the new enforcement scripts (see `scripts/README.md`).

