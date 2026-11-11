# skill-3d-auto-fabrik

> `fabrik`: Fäbrik (_k-a:_/fábrica) — factory, in German and Spanish.

> _anti-ai/slop_: this repository was written by humans. The agent may read it.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skill format](https://img.shields.io/badge/Agent%20Skills-standard-7c3aed.svg)](https://agentskills.io/specification.md)

**From mesh file to supervised print, with a human in the loop.**

`3d-auto-fabrik` is an **Agent Skills**-standard, platform-agnostic skill that
orchestrates two MCP servers to take a 3D model from a mesh file to a
supervised Klipper print:

| Server | Job | Source |
| --- | --- | --- |
| `mcp-cura` | mesh inspect/repair, profile resolve/verify, CuraEngine slice, G-code review | sibling repository — builds from source, not yet published to crates.io/GitHub |
| [`mcp-moonraker`](https://github.com/martinsgmx/mcp-moonraker) | printer state, temperatures, camera, pause/resume/cancel, print start, job queue | published sibling repository |

This repository contains **the skill only** — the servers live in their own
repositories and are installed separately. The skill teaches any
skills-compatible agent the correct, safe pipeline between them — including
the approval protocol for destructive actions — so the agent verifies (mesh,
profile, G-code, connection) before it ever heats a nozzle.

## Why a skill and not just two servers?

The servers are the hands; the skill is the checklist and the conscience.
Without it, a capable agent will happily slice with a failing profile, skip
G-code verification, or print without asking. The skill encodes the ordering,
the verification gates, and the approval protocol that keep a print from
becoming a fire — in a portable folder any compliant client can load.

The pipeline in one line:

```text
import → inspect → resolve/verify profile → slice → G-code review
      → human checkpoint → transfer → confirm → print → monitor
```

Each stage names the exact tool to call; each gate names what must be true
before moving on. See [docs/architecture.md](docs/architecture.md) for the
full data flow.

## What you need

- A Klipper printer with [Moonraker](https://moonraker.readthedocs.io/en/latest/)
  reachable over HTTP (default `http://127.0.0.1:7125`).
- [CuraEngine](https://github.com/Ultimaker/CuraEngine) for slicing — comes
  with a normal Cura installation, or use the AppImage fetch script shipped in
  the mcp-cura repo. Not needed for mesh-only work.
- Rust 1.89+ to build the two servers from source.
- An agent client that supports both Agent Skills and MCP (OpenCode, Claude
  Code/Desktop, Gemini CLI, Cursor, Windsurf, …).
- Python 3 only for this repo's tooling (validator, evals) — not for using
  the skill itself.

## Repository layout

```text
skill-3d-auto-fabrik/
├── skills/3d-auto-fabrik/    ← the installable skill (SKILL.md + references + scripts)
├── docs/                     ← human documentation (safety, configuration, platforms, architecture, FAQ)
├── examples/                 ← ready-to-copy MCP client snippets (opencode, claude, gemini, cursor, windsurf)
├── evals/                    ← test prompts for skill evaluation
├── scripts/                  ← repo tooling (skill validator, tool-reference generator)
└── .github/                  ← CI (skill validation), issue & PR templates
```

## Quickstart

Both MCP servers ship as Rust binaries built from their sibling
repositories — this workspace layout is the supported install path:

```text
repos/
├── skill-3d-auto-fabrik/   ← this repository
├── mcp-cura/               ← the slicing MCP server
└── mcp-moonraker/          ← the printer MCP server (git clone https://github.com/martinsgmx/mcp-moonraker)
```

1. **Build and install both servers** (requires Rust 1.89+):

   ```sh
   cargo install --path ../mcp-cura
   cargo install --path ../mcp-moonraker
   mcp-cura doctor          # engine, workspace, profiles
   mcp-moonraker doctor     # Moonraker connectivity, Klipper state, cameras
   ```

   Adjust the paths to wherever the siblings live on your machine. A healthy
   `mcp-cura doctor` ends with something like (abbreviated):

   ```text
   [OK  ] configuration    transport=Stdio, engine_runner=Binary, approval=InBand
   [OK  ] profiles         0 definitions, 6 profiles across 3 directories
   [OK  ] tools            32 registered: 25 immediate, 2 approval-gated, ...
   Result: OK (1 warning(s))
   ```

   `mcp-moonraker doctor` reports whether Moonraker answers, the Klipper
   state (`ready` vs `error`/`shutdown`), and camera configuration (counts
   and states are machine-specific):

   ```text
   [OK  ] Moonraker        reachable at http://127.0.0.1:7125 (Moonraker v0.11.0, API 1.5.0)
   [WARN] Klipper          state=error: mcu 'mcu': Unable to connect ...
   [OK  ] cameras          1 configured, 1 enabled, 1 with snapshots
   ```

   (A `Klipper state=error` warning means the printer's MCU is not
   connected — usually a powered-off printer or a firmware fault to fix on
   the printer itself, not in this stack.) See
   [docs/configuration.md](docs/configuration.md) for TOML config,
   environment variables and approval modes.

2. **Register them as MCP servers** in your client —
   copy-paste snippets for OpenCode, Claude, Gemini CLI, Cursor and Windsurf
   live in [docs/platforms.md](docs/platforms.md) and [examples/](examples/).
   Tools are prefixed server-side (`cura_*`, `moonraker_*`), so they don't
   collide whichever client key you register them under.

3. **Install the skill.** There is nothing to build — the skill is markdown.
   Point your agent at `skills/3d-auto-fabrik/`:

   | Client | Install |
   | --- | --- |
   | OpenCode | `cp -r skills/3d-auto-fabrik ~/.config/opencode/skills/` (or project `.opencode/skills/`, or `.agents/skills/`) |
   | Claude Code | `cp -r skills/3d-auto-fabrik ~/.claude/skills/` (or project `.claude/skills/`) |
   | Gemini CLI | `cp -r skills/3d-auto-fabrik ~/.agents/skills/` — or `gemini skills install <this-repo-url> --consent --path skills/3d-auto-fabrik` |
   | Generic Agent Skills clients | copy/symlink `skills/3d-auto-fabrik/` into the client's skills directory |

   The skill ID is `3d-auto-fabrik` (the folder name must match `name`).
   Symlinking instead of copying works well for development — the client
   picks up edits to `SKILL.md` without reinstalling.

4. **Ask your agent**, for example:

   > "Slice ~/Downloads/bracket.stl for the Voron in PETG, 0.2 quality,
   > then print it after I confirm the G-code."

   The agent should import → inspect → resolve/verify → slice → verify
   G-code → show you the estimate → wait for your go → transfer → confirm →
   start the print. If it tries to skip a gate, point it at
   `references/safety-approvals.md`.

5. **Verify the chain end to end** before trusting a real print:

   ```sh
   sh skills/3d-auto-fabrik/scripts/check-setup.sh   # binaries on PATH, versions, tool counts
   ```

   Then ask the agent: *"run mcp-moonraker verify connection and tell me the
   Klipper state."* A clean answer means skill → client → servers → printer all
   work.

More documentation: [architecture](docs/architecture.md) ·
[configuration](docs/configuration.md) · [platforms](docs/platforms.md) ·
[safety](docs/safety.md) · [FAQ](docs/faq.md).

## Platform notes

This repo treats **OpenCode**, **Claude Code / Claude Desktop**, **Gemini
CLI**, **Cursor**, **Windsurf** and other Agent Skills–compatible clients as
equal citizens. The skill itself is plain markdown + YAML (the open
[Agent Skills](https://agentskills.io) format); only the install path and the
MCP registration differ per client — all covered in
[docs/platforms.md](docs/platforms.md).

Claude.ai (the web app) doesn't launch local stdio binaries; use Claude Code
or Claude Desktop with `claude_desktop_config.json`, or put the servers
behind HTTP transport with authentication. See the platforms doc.

## Safety

This software drives a heated machine. Read
[docs/safety.md](docs/safety.md) — the short version: destructive actions
require explicit double confirmation, temperatures are capped by local
policy, and `moonraker_emergency_stop` exists for real emergencies. The
skill will not bypass these gates, and neither should you.

If you find a way past a gate, that is a security vulnerability, not a bug —
see [SECURITY.md](SECURITY.md) and do not open a public issue.

## Status

`v0.1.0` — pre-1.0. The skill, tool catalogs and docs may change between
releases; pin a commit if you need stability. Notable changes are tracked in
[CHANGELOG.md](CHANGELOG.md).

## Development

```sh
python3 scripts/validate-skill.py        # validate the skill
python3 scripts/generate-tool-reference.py   # refresh references after server upgrades
python3 scripts/grade-eval.py            # grade an eval iteration in ../skill-3d-auto-fabrik-workspace
sh skills/3d-auto-fabrik/scripts/check-setup.sh   # verify binaries on PATH
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Test prompts for evaluating the
skill live in [evals/evals.json](evals/evals.json); the harness, safety
rails, and grading notes are in [evals/README.md](evals/README.md).

## License

[MIT](LICENSE) © 2026 skill-3d-auto-fabrik contributors.
