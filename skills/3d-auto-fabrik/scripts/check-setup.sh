#!/bin/sh
# check-setup.sh — read-only sanity check for the mcp-cura / mcp-moonraker pair.
# Verifies binaries exist, reports versions, counts exposed tools.
# Does NOT contact the printer or the CuraEngine; `doctor` does that.
#
# Usage: sh scripts/check-setup.sh

set -eu

fail=0

check() {
    name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        ver=$("$name" --version 2>/dev/null || echo "unknown")
        tools=$("$name" tools 2>/dev/null | tail -n 1 || echo "tools: failed to list")
        printf 'ok    %-16s %s\n' "$name" "$ver"
        printf '      %s\n' "$tools"
    else
        printf 'MISS  %-16s not found on PATH\n' "$name"
        fail=1
    fi
}

echo "== 3d-auto-fabrik setup check =="
check mcp-cura
check mcp-moonraker

if [ "$fail" -ne 0 ]; then
    echo
    echo "Install the missing server(s) from the sibling repositories, e.g.:"
    echo "  cargo install --path /path/to/mcp-cura"
    echo "  cargo install --path /path/to/mcp-moonraker"
    echo "then re-run this script. See docs/configuration.md in the repository."
    exit 1
fi

cat <<'EOF'

Both servers found. Next steps:
  1. mcp-cura doctor          — engine, workspace, profiles
  2. mcp-moonraker doctor     — Moonraker connectivity, Klipper state, cameras
  3. Register both as MCP servers in your agent client (docs/platforms.md).
EOF
