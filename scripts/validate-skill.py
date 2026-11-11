#!/usr/bin/env python3
"""Validate the 3d-auto-fabrik skill against the Agent Skills spec.

Checks (stdlib only):
  * skills/3d-auto-fabrik/SKILL.md exists
  * frontmatter is present, name/description present and well-formed
  * name matches the parent directory, allowed charset, 1-64 chars
  * description 1-1024 chars and mentions key trigger terms
  * body under 500 lines (progressive-disclosure budget)
  * every file referenced from SKILL.md exists
  * LICENSE exists at repo root

Exits non-zero on any failure. Run from the repository root:

  python3 scripts/validate-skill.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "3d-auto-fabrik"
SKILL_MD = SKILL_DIR / "SKILL.md"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def main() -> int:
    if not SKILL_MD.is_file():
        fail(f"missing {SKILL_MD.relative_to(REPO_ROOT)}")
        return report()

    text = SKILL_MD.read_text(encoding="utf-8")

    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        fail("SKILL.md must start with YAML frontmatter delimited by --- lines")
        return report()

    front, body = m.group(1), m.group(2)

    def field(name: str) -> str | None:
        # minimal YAML: scalar fields only (our frontmatter uses plain or folded scalars)
        fm = re.search(rf"^{name}:\s*(?:>-?\n((?:[ \t]+.*\n?)+)|([^\n]*))", front, re.M)
        if not fm:
            return None
        if fm.group(1):  # folded block
            return " ".join(fm.group(1).split())
        return fm.group(2).strip().strip("\"'")

    name = field("name")
    if not name:
        fail("frontmatter missing required field: name")
    else:
        if len(name) > 64 or not NAME_RE.match(name):
            fail(f"name {name!r} must be 1-64 lowercase alphanumerics and hyphens")
        elif name != SKILL_DIR.name:
            fail(f"name {name!r} must match the parent directory {SKILL_DIR.name!r}")
        else:
            ok(f"name {name!r} valid and matches directory")

    desc = field("description")
    if not desc:
        fail("frontmatter missing required field: description")
    else:
        if not 1 <= len(desc) <= 1024:
            fail(f"description is {len(desc)} chars; must be 1-1024")
        else:
            ok(f"description length {len(desc)} ok")
        for term in ("mcp-cura", "mcp-moonraker"):
            if term not in desc:
                fail(f"description should mention {term} to anchor triggering")

    body_lines = body.count("\n") + 1
    if body_lines > 500:
        fail(f"SKILL.md body is {body_lines} lines; keep under 500 (progressive disclosure)")
    else:
        ok(f"body {body_lines} lines (< 500)")

    for ref in sorted(set(re.findall(r"\]\((references/[^)#\s]+|scripts/[^)#\s]+)\)", body))):
        if not (SKILL_DIR / ref).exists():
            fail(f"referenced file missing: {ref}")
        else:
            ok(f"reference exists: {ref}")

    if not (REPO_ROOT / "LICENSE").is_file():
        fail("LICENSE missing at repository root")
    else:
        ok("LICENSE present")

    return report()


def report() -> int:
    print()
    if failures:
        print(f"{len(failures)} problem(s) found")
        return 1
    print("skill is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
