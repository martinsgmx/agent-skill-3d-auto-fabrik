# skill-3d-auto-fabrik

> `fabrik`: Fäbrik (_k-a:_/fábrica) — factory, in German and Spanish.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skill format](https://img.shields.io/badge/Agent%20Skills-standard-7c3aed.svg)](https://agentskills.io/specification.md)

**From mesh file to supervised print, with a human in the loop.**

`3d-auto-fabrik` is an **Agent Skills**-standard, platform-agnostic skill that
orchestrates three MCP servers to take a 3D model from a mesh file to a
supervised Klipper print:

| Server                 | Job                                                                              | License    | Repository                                                                           |
| ---------------------- | -------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------ |
| `mcp-orca` (preferred) | OrcaSlicer presets, mesh inspect/transform/merge, slice jobs, G-code inspect     | Apache-2.0 | [martinsgmx/mcp-orca](https://github.com/martinsgmx/mcp-orca)                         |
| `mcp-cura` (fallback)  | CuraEngine profiles, richer mesh repair, slice jobs, G-code verify/prepare       | MIT        | [martinsgmx/mcp-cura](https://github.com/martinsgmx/mcp-cura)                         |
| `mcp-moonraker`        | printer state, temperatures, camera, pause/resume/cancel, print start, job queue | MIT        | [martinsgmx/mcp-moonraker](https://github.com/martinsgmx/mcp-moonraker)              |

This repository contains **the skill only** — the servers live in their own
repositories and are installed separately. The skill teaches any
skills-compatible agent the correct, safe pipeline between them — including
the approval protocol for destructive actions — so the agent verifies (mesh,
profile, G-code, connection) before it ever heats a nozzle.

## Why a skill and not just three servers?

The servers are the hands; the skill is the checklist and the conscience.
Without it, a capable agent will happily slice with a failing profile, skip
G-code review, or print without asking. The skill encodes the ordering, the
verification gates, and the approval protocol that keep a print from becoming
a fire — in a portable folder any compliant client can load.

The pipeline in one line:

```text
workspace + discovery → choose engine → import → inspect → resolve profile
→ slice → G-code review → human checkpoint → transfer → confirm
→ queue or print → monitor → cleanup
```

Ready-made G-code takes a shorter branch: validate it against the selected
printer and stop, without slicing or touching the printer unless you ask.

Each stage names the exact tool to call; each gate names what must be true
before moving on. See [docs/architecture.md](docs/architecture.md) for the
full data flow.

## Engine selection

mcp-orca is the default. If it is not running, not installed, or has no
slicer engine configured, the skill falls back to mcp-cura for the whole job —
same stages, same gates, different tool names. It never mixes artifact ids
between servers and never silently switches mid-job.

The capability differences matter: Orca has inspect/transform/merge and a
G-code **inspect** tool; Cura adds boolean/offset/remesh/decimate, profile
verify, and G-code **verify/prepare**. Orca's inspect reports statistics only —
it does **not** scan for dangerous commands, so that check needs Cura (or a
manual header/footer read). The skill tells the agent when a job needs the
fallback. Details:
[skills/3d-auto-fabrik/references/engine-selection.md](skills/3d-auto-fabrik/references/engine-selection.md).

## Inputs and configuration

Give the agent a model path, a folder of models, or an http(s) URL to a ZIP.
Each job gets a unique temp workspace
(`${TMPDIR:-/tmp}/3d-auto-fabrik/job_…`); archives are extracted there,
models are discovered and listed, and you pick which one(s) to use. A `.3mf`
is one model, found G-code is validated, and nothing is auto-selected or
auto-deleted. See
[skills/3d-auto-fabrik/references/job-workspace.md](skills/3d-auto-fabrik/references/job-workspace.md).

Printers and materials come from the **live MCP configuration** first
(`orca_server_info`/`orca_doctor`/`orca_profile_list`, or Cura equivalents,
plus read-only `moonraker_config`/`moonraker_server_info`/
`moonraker_policy_info`). Your labels map to exact preset ids in
`~/.config/3d-auto-fabrik/config.yaml` (optional `./3d-auto-fabrik.yaml`
override); no secrets go in that file. If a label is unmapped, the agent asks.
See
[skills/3d-auto-fabrik/references/printer-materials.md](skills/3d-auto-fabrik/references/printer-materials.md).

## What you need

- A Klipper printer with [Moonraker](https://moonraker.readthedocs.io/en/latest/)
  reachable over HTTP (default `http://127.0.0.1:7125`).
- [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) for the preferred
  engine, **or** [CuraEngine](https://github.com/Ultimaker/CuraEngine) for the
  fallback. Mesh-only work needs neither.
- The three MCP servers installed and on your PATH — see Quickstart below. The
  skill does not install or configure them.
- An agent client that can register stdio MCP servers and load Agent Skills —
  or a persistent-instructions file you can paste `SKILL.md` into (OpenCode,
  Claude Code/Desktop, Gemini CLI, Cursor, Windsurf, …).
- Python 3 only for this repo's tooling (validator, evals) — not for using
  the skill itself.

## Repository layout

```text
skill-3d-auto-fabrik/
├── commands/                 ← optional slash-command prompts (e.g. /setup-3d-fabrik)
├── skills/3d-auto-fabrik/    ← the installable skill (SKILL.md + references + scripts)
├── docs/                     ← human documentation (safety, configuration, platforms, architecture, FAQ)
├── examples/                 ← ready-to-copy MCP client snippets (opencode, claude, gemini, cursor, windsurf)
├── evals/                    ← test prompts for skill evaluation
├── scripts/                  ← repo tooling (skill validator, tool-reference generator)
└── .github/                  ← CI (skill validation), issue & PR templates
```

## Quickstart

The three MCP servers are installed and configured separately. Follow the
instructions in each server's own repository — this skill does not install or
configure them, it only needs their binaries on your PATH:

- [mcp-orca](https://github.com/martinsgmx/mcp-orca) — preferred slicing server.
- [mcp-cura](https://github.com/martinsgmx/mcp-cura) — optional fallback.
- [mcp-moonraker](https://github.com/martinsgmx/mcp-moonraker) — printer server.

A missing slicer binary is only a warning: slicing stays disabled until an
engine is configured. `Klipper state=error` means the printer's MCU is not
connected, not a problem in this stack. For configuration details, see
[docs/configuration.md](docs/configuration.md) and the server repositories.

1. **Register the servers as MCP servers** in your client —
   copy-paste snippets for OpenCode, Claude, Gemini CLI, Cursor and Windsurf
   live in [docs/platforms.md](docs/platforms.md) and [examples/](examples/).
   Tools are prefixed server-side (`orca_*`, `cura_*`, `moonraker_*`), so they
   don't collide whichever client key you register them under.

2. **Install the skill.** There is nothing to build — the skill is markdown.
   Point your agent at `skills/3d-auto-fabrik/`:

   | Client                       | Install                                                                                                                                                                      |
   | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | OpenCode                     | `cp -r skills/3d-auto-fabrik ~/.config/opencode/skills/` (or project `.opencode/skills/`, or `.agents/skills/`)                                                              |
   | Claude Code                  | `cp -r skills/3d-auto-fabrik ~/.claude/skills/` (or project `.claude/skills/`)                                                                                               |
   | Gemini CLI                   | `cp -r skills/3d-auto-fabrik ~/.agents/skills/` — or `gemini skills install https://github.com/martinsgmx/agent-skill-3d-auto-fabrik --consent --path skills/3d-auto-fabrik` |
   | Generic Agent Skills clients | copy/symlink `skills/3d-auto-fabrik/` into the client's skills directory                                                                                                     |

   The skill ID is `3d-auto-fabrik` (the folder name must match `name`).
   Symlinking instead of copying works well for development — the client
   picks up edits to `SKILL.md` without reinstalling.

   **Optional: install the setup command.** If your client supports slash
   commands, copy `commands/setup-3d-fabrik.md` so you can run
   `/setup-3d-fabrik`:

   | Client        | Command install                                                                                                            |
   | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
   | OpenCode      | `cp commands/setup-3d-fabrik.md ~/.config/opencode/commands/` (or project `.opencode/commands/`)                           |
   | Claude Code   | `cp commands/setup-3d-fabrik.md ~/.claude/commands/` (or project `.claude/commands/`)                                      |
   | Other clients | copy the file into the client's command/prompt directory, or paste its contents as a saved prompt named `/setup-3d-fabrik` |

3. **Run the setup check.** Before the first real job, verify the local
   environment and MCP health:

   ```sh
   sh skills/3d-auto-fabrik/scripts/check-setup.sh   # binaries on PATH, versions, tool counts
   ```

   Then, in your agent, run `/setup-3d-fabrik` (if installed) or ask:

   > "Run the 3d-auto-fabrik setup check. Verify mcp-orca, mcp-cura, and
   > mcp-moonraker; report what's ready; then help me set default printer,
   > material, and profile mappings."

   The setup flow is read-only: it checks doctors/policies/profiles/connectivity,
   reports a readiness table, and only writes `~/.config/3d-auto-fabrik/config.yaml`
   (or `./3d-auto-fabrik.yaml`) after you explicitly confirm the proposed
   defaults. It never edits server configs, never stores secrets, and never
   touches hardware.

4. **Ask your agent to do real work**, for example:

   > "Slice ~/Downloads/bracket.stl for the Voron in PETG, 0.2 process,
   > then print it after I confirm the G-code."

   The agent should choose an engine, import → inspect → resolve → slice →
   review G-code → show you the estimate → wait for your go → transfer →
   confirm → start the print. If it tries to skip a gate, point it at
   [skills/3d-auto-fabrik/references/safety-approvals.md](skills/3d-auto-fabrik/references/safety-approvals.md).

## Usage examples

```text
/setup-3d-fabrik
```

Checks binaries, MCP doctor/engine/policy/profile readiness, Moonraker
connectivity, and optionally writes confirmed defaults to
`~/.config/3d-auto-fabrik/config.yaml`.

```text
Slice ~/models/benchy.3mf for my Voron in PLA, 0.2mm, then wait for my
confirmation before printing.
```

Runs the normal pipeline: workspace/import → inspect → profile resolve → slice
→ G-code review → explicit checkpoint → transfer → approval-gated print.

```text
Check this G-code against my printer and PETG limits, but do not print it:
~/Downloads/part.gcode
```

Uses the ready-made G-code branch: import/review/compatibility PASS-FAIL report,
no queue, no transfer, no print.

```text
I have a ZIP URL with model files. Download it, show me what models it
contains, and let me pick which one to slice.
```

Uses the job-workspace discovery flow: unique temp workspace, safe ZIP extract,
model listing, explicit user selection before import.

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

## Troubleshooting

- **A tool "doesn't exist"** — check client-side tool filters first, then the
  server's policy. [docs/platforms.md](docs/platforms.md) lists common filters;
  `orca_policy_info` / `cura_policy_info` / `moonraker_policy_info` show the
  server side.
- **Slicing fails but `doctor` looks fine** — read `orca_engine_info` /
  `cura_engine_info`: `doctor`'s overall `ok` can hide an unwired engine. The
  session guide covers engine wiring, custom `slice_command`, imports, G-code
  review, transfer and print:
  [skills/3d-auto-fabrik/references/troubleshooting_mcps.md](skills/3d-auto-fabrik/references/troubleshooting_mcps.md).
- **Refused imports/exports, profile-list misses, G-code discrepancies** —
  [skills/3d-auto-fabrik/references/troubleshooting.md](skills/3d-auto-fabrik/references/troubleshooting.md).

## Safety

This software drives a heated machine. Read
[docs/safety.md](docs/safety.md) — the short version: destructive actions
require explicit approval, temperatures are capped by local policy, and
`moonraker_emergency_stop` exists for real emergencies. The skill will not
bypass these gates, and neither should you.

If you find a way past a gate, that is a security vulnerability, not a bug —
see [SECURITY.md](SECURITY.md) and do not open a public issue.

## Status

`0.2.5` — released 2026-11-24, tagged `v0.2.5`. See
[CHANGELOG.md](CHANGELOG.md) for release history. This is pre-1.0: the skill,
tool catalogs and docs may change between releases; pin a commit or tag if you
need stability.

## Development

```sh
python3 scripts/validate-skill.py             # validate the skill
python3 scripts/generate-tool-reference.py    # refresh references after server upgrades
python3 scripts/grade-eval.py iteration-1     # grade ../skill-3d-auto-fabrik-workspace/iteration-1
sh skills/3d-auto-fabrik/scripts/check-setup.sh   # verify binaries on PATH
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Test prompts for evaluating the
skill live in [evals/evals.json](evals/evals.json); the harness, safety
rails, and grading notes are in [evals/README.md](evals/README.md). The
harness calls the servers through `evals/mcp-call.py` (stdio JSON-RPC).

## License

[MIT](LICENSE) © 2026 skill-3d-auto-fabrik contributors. The companion
servers keep their own licenses: mcp-orca is Apache-2.0; mcp-cura and
mcp-moonraker are MIT.
