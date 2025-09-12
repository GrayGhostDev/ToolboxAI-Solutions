#!/usr/bin/env sh
# Terminal 3: Roblox Bridge Server (deprecated, replaced by terminal3_start.sh)
set -eu
# shellcheck source=common/lib.sh
. "$(cd "$(dirname "$0")"/.. && pwd -P)/scripts/common/lib.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")"/.. && pwd -P)/common/lib.sh"

echo "This script has been superseded by scripts/terminal3_start.sh"
echo "Invoking terminal3_start.sh for compatibility..."
exec "$PROJECT_ROOT/scripts/terminal3_start.sh" "$@"
