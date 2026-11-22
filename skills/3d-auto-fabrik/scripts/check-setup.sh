#!/bin/sh
# check-setup.sh — read-only sanity check for the mcp-orca / mcp-cura /
# mcp-moonraker trio. Verifies binaries exist, reports versions, counts
# exposed tools. Does NOT contact the printer or the slicer engine; each
# server's `doctor` does that.
#
# Usage: sh scripts/check-setup.sh

set -eu

fail=0
slicers=0

check() {
    name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        ver=$("$name" --version 2>/dev/null || echo "unknown")
        tools=$("$name" tools 2>/dev/null | grep -Ec '^[a-z][a-z0-9_]*[[:space:]]' || true)
        printf 'ok    %-16s %s (%s tools)\n' "$name" "$ver" "$tools"
    else
        printf 'MISS  %-16s not found on PATH\n' "$name"
        return 1
    fi
}

echo "== 3d-auto-fabrik setup check =="
check mcp-orca && slicers=$((slicers + 1)) || true
check mcp-cura && slicers=$((slicers + 1)) || true
check mcp-moonraker || fail=1

if [ "$slicers" -eq 0 ]; then
    echo
    echo "No slicing server found. Install mcp-orca (preferred) or mcp-cura:"
    echo "  cargo install --path /path/to/mcp-orca"
    echo "  cargo install --path /path/to/mcp-cura"
    fail=1
fi

if [ "$fail" -ne 0 ]; then
    echo
    echo "Install the missing server(s) from the sibling repositories:"
    echo "  cargo install --path /path/to/mcp-orca"
    echo "  cargo install --path /path/to/mcp-cura"
    echo "  cargo install --path /path/to/mcp-moonraker"
    echo "then re-run this script. See docs/configuration.md in the repository."
    exit 1
fi

cat <<'EOF'

All required servers found. Next steps:
  1. mcp-orca doctor           — engine preset/binary, workspace, profiles
     (if Orca is not usable, the skill falls back to mcp-cura)
  2. mcp-cura doctor           — CuraEngine, workspace, profiles
  3. mcp-moonraker doctor      — Moonraker connectivity, Klipper state, cameras
  4. In your agent, run /setup-3d-fabrik (commands/setup-3d-fabrik.md) to get
     a readiness report and optionally confirm default printer/profile mappings.
  5. Register the servers as MCP servers in your agent client (docs/platforms.md).
EOF
