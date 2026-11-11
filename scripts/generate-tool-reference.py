#!/usr/bin/env python3
"""Regenerate the tool-catalog references in skills/3d-auto-fabrik/references/.

Runs `mcp-cura tools --json` and `mcp-moonraker tools --json` and rewrites:

  skills/3d-auto-fabrik/references/mcp-cura-tools.md
  skills/3d-auto-fabrik/references/mcp-moonraker-tools.md

Usage (from the repository root):

  python3 scripts/generate-tool-reference.py

Requires mcp-cura and mcp-moonraker on PATH. No third-party dependencies.
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


def fetch(binary: str) -> dict:
    if shutil.which(binary) is None:
        sys.exit(f"error: {binary} not found on PATH")
    out = subprocess.run([binary, "tools", "--json"], check=True,
                         capture_output=True, text=True).stdout
    return json.loads(out)


def render(binary: str, title: str, intro: str, out_path: Path) -> None:
    data = fetch(binary)
    rows = []
    for t in sorted(data["tools"], key=lambda t: (ORDER[t["risk"]], t["name"])):
        args = ", ".join(t["arguments"]) or "—"
        desc = t["description"].replace("|", "\\|").replace("\n", " ")
        rows.append(f"| `{t['name']}` | {t['risk']} | {t['gate']} | `{args}` | {desc} |")
    out_path.write_text(
        TEMPLATE.format(title=title, binary=binary, intro=intro,
                        rows="\n".join(rows)),
        encoding="utf-8")
    print(f"wrote {out_path.relative_to(REPO_ROOT)} ({len(data['tools'])} tools)")


def main() -> None:
    render(
        "mcp-cura",
        "mcp-cura tool catalog",
        "Pipeline order: import → mesh ops → profile resolve/verify → slice → "
        "G-code review → export/delete. Nothing here contacts the printer.",
        REFERENCES / "mcp-cura-tools.md",
    )
    render(
        "mcp-moonraker",
        "mcp-moonraker tool catalog",
        "Read-only tools first (`printer_status`, `temperatures`, `server_info`), "
        "reversible mutations next, double-confirmed destructive tools last. "
        "`moonraker_emergency_stop` bypasses gates by design.",
        REFERENCES / "mcp-moonraker-tools.md",
    )


if __name__ == "__main__":
    main()
