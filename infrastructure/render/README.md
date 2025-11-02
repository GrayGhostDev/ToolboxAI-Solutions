# Render Deployment Assets

This directory centralizes the Render.com blueprints and helper tooling that back the production `render.yaml` at the repository root.

## Contents

- `render.production.yaml` – canonical production blueprint (root `render.yaml` symlinks here).
- `render.staging.yaml` – lighter staging blueprint that mirrors the production structure with reduced plans.
- `sync-render-config.sh` – helper that recreates the root `render.yaml` symlink or copies any blueprint into place for environments that cannot use symlinks (e.g., Windows without developer mode).

## Usage

```bash
# Ensure the root render.yaml targets the production blueprint via symlink
cd infrastructure/render
./sync-render-config.sh --env production --symlink

# Copy the staging config into render.yaml (overwrites symlink) when testing staged resources
./sync-render-config.sh --env staging --copy
```

The deployment script (`scripts/deployment/deploy-render.sh`) automatically picks up `render.yaml` from the repository root. Always regenerate the root file after editing any blueprint to keep Render deployments in sync.

## Adding New Services

1. Update `render.production.yaml` (and staging if applicable).
2. Run `./sync-render-config.sh --env production --symlink` so the root file reflects the new definition.
3. Commit both the blueprint and the refreshed `render.yaml` symlink to version control.

## Validation

- `scripts/deployment/deploy-render.sh validate` – runs structural checks plus dependency validation.
- `renderctl` CLI (if installed) – `renderctl blueprint lint render.yaml`.

Keep Render service names aligned with Docker Compose service intent so observability, incidents, and documentation stay consistent across environments.
