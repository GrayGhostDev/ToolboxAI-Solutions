#!/bin/bash
# Render configuration synchronizer
# Ensures the repository root render.yaml tracks the desired blueprint

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET_FILE="$PROJECT_ROOT/render.yaml"

ENVIRONMENT="production"
MODE="symlink" # symlink | copy

usage() {
  cat <<'EOF'
Usage: sync-render-config.sh [options]

Options:
  --env <production|staging>  Blueprint to promote (default: production)
  --copy                      Copy file contents instead of creating a symlink
  --symlink                   Force recreation of the symlink (default)
  -h, --help                  Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENVIRONMENT="${2:-}"
      shift 2
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --symlink)
      MODE="symlink"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

case "$ENVIRONMENT" in
  production)
    SOURCE_FILE="$SCRIPT_DIR/render.production.yaml"
    ;;
  staging)
    SOURCE_FILE="$SCRIPT_DIR/render.staging.yaml"
    ;;
  *)
    echo "Unsupported environment: $ENVIRONMENT" >&2
    exit 1
    ;;
esac

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "Source blueprint not found: $SOURCE_FILE" >&2
  exit 1
fi

if [[ "$MODE" == "symlink" ]]; then
  if [[ -e "$TARGET_FILE" || -L "$TARGET_FILE" ]]; then
    rm -f "$TARGET_FILE"
  fi
  ln -s "${SOURCE_FILE#$PROJECT_ROOT/}" "$TARGET_FILE"
  echo "Symlinked $TARGET_FILE -> ${SOURCE_FILE#$PROJECT_ROOT/}"
else
  cp "$SOURCE_FILE" "$TARGET_FILE"
  echo "Copied $SOURCE_FILE to $TARGET_FILE"
fi
