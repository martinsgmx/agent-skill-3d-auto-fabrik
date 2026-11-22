#!/usr/bin/env python3
"""Regenerate the tool-catalog references in skills/3d-auto-fabrik/references/.

Runs `mcp-orca tools --json`, `mcp-cura tools --json` and
`mcp-moonraker tools --json`, then rewrites:

  skills/3d-auto-fabrik/references/mcp-orca-tools.md
  skills/3d-auto-fabrik/references/mcp-cura-tools.md
  skills/3d-auto-fabrik/references/mcp-moonraker-tools.md

Missing binaries are skipped with a warning, so a Cura-only or Orca-only
machine can still refresh the catalog it has. The script fails only when no
catalog could be generated.

Usage (from the repository root):

  python3 scripts/generate-tool-reference.py

Requires the corresponding server binaries on PATH. No third-party
dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = REPO_ROOT / "skills" / "3d-auto-fabrik" / "references"

TEMPLATE = """# {title}

> Generated from `{binary} tools --json` by `scripts/generate-tool-reference.py`.
> Regenerate after any server upgrade. Risk and gate come from the server's
> own policy engine — do not hand-edit this table.

Risk tiers: `read` (no mutation) → `low` → `medium` → `high` → `critical`.
Gates: `policy` (local safety policy), `local` (local info only),
`confirm` (explicit confirmation), `emergency` (emergency only).

{intro}

| Tool | Risk | Gate | Arguments | Description |
| --- | --- | --- | --- | --- |
{rows}
"""

ORDER = {"read": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def fetch(binary: str) -> dict | None:
    if shutil.which(binary) is None:
        print(f"warning: {binary} not found on PATH; skipping", file=sys.stderr)
        return None
    out = subprocess.run([binary, "tools", "--json"], check=True,
                         capture_output=True, text=True).stdout
    return json.loads(out)


def render(binary: str, title: str, intro: str, out_path: Path) -> bool:
    data = fetch(binary)
    if data is None:
        return False
    rows = []
    for t in sorted(data["tools"], key=lambda t: (ORDER.get(t["risk"], 9), t["name"])):
        args = ", ".join(t["arguments"]) or "—"
        desc = t["description"].replace("|", "\\|").replace("\n", " ")
        rows.append(f"| `{t['name']}` | {t['risk']} | {t['gate']} | `{args}` | {desc} |")
    out_path.write_text(
        TEMPLATE.format(title=title, binary=binary, intro=intro,
                        rows="\n".join(rows)),
        encoding="utf-8")
    print(f"wrote {out_path.relative_to(REPO_ROOT)} ({len(data['tools'])} tools)")
    return True


def main() -> int:
    results = [
        render(
            "mcp-orca",
            "mcp-orca tool catalog",
            "Pipeline order: import → mesh inspect/transform/merge → profile "
            "resolve → slice → G-code inspect → export/delete. Nothing here "
            "contacts the printer. Export and delete require an approval "
            "request plus `orca_approval_decide`, then a retry of the "
            "identical call.",
            REFERENCES / "mcp-orca-tools.md",
        ),
        render(
            "mcp-cura",
            "mcp-cura tool catalog",
            "Pipeline order: import → mesh ops → profile resolve/verify → slice → "
            "G-code review → export/delete. Nothing here contacts the printer.",
            REFERENCES / "mcp-cura-tools.md",
        ),
        render(
            "mcp-moonraker",
            "mcp-moonraker tool catalog",
            "Read-only tools first (`printer_status`, `temperatures`, `server_info`), "
            "reversible mutations next, double-confirmed destructive tools last. "
            "`moonraker_emergency_stop` bypasses gates by design.",
            REFERENCES / "mcp-moonraker-tools.md",
        ),
    ]
    if not any(results):
        print("error: no MCP server binaries found on PATH", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
