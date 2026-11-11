# Architecture

`3d-auto-fabrik` is a skill, not a program. It carries no runtime of its own —
it is the load-bearing knowledge between two MCP servers and the agent that
drives them.

## The three repositories

```text
repos/
├── skill-3d-auto-fabrik   this skill (the orchestrator)
├── mcp-cura               the slicing MCP server (mesh, CuraEngine, G-code)
└── mcp-moonraker          the printer MCP server (Klipper via Moonraker)
```

All three are MIT-licensed companions. The MCP servers are deliberately
independent of each other and of this skill: each works without this skill,
and this skill is useless without both.

## Trust boundaries

```text
┌─────────────────────────────┐        ┌──────────────────────────────┐
│          mcp-cura           │        │         mcp-moonraker        │
│                             │        │                              │
│  STL/3MF ──► import         │        │  Moonraker HTTP API          │
│      ──► mesh inspect/fix   │        │      └► state, temps, camera │
│      ──► profile resolve    │        │      └► heaters, fans, motion│
│      ──► verify ──► slice   │        │      └► print control, queue │
│      ──► G-code inspect/    │        │                              │
│          verify ──► prepare │        │  host admin (off by default) │
│                             │        │  raw G-code (off by default) │
│  workspace:                 │        │                              │
│  ~/.local/share/mcp-cura    │        │  safety policy: read-only?   │
│  content-addressed          │        │  temp caps, approval mode    │
└─────────────┬───────────────┘        └───────────────▲──────────────┘
              │                                        │
              │   G-code artifact                      │  gcodes root
              └────────── approval-gated handoff ──────┘
              (cura_artifact_export, or the user copies)
```

Facts that follow:

1. **mcp-cura never contacts the printer.** Its outputs are files in its
   content-addressed workspace.
2. **mcp-moonraker never slices.** It trusts the `gcodes` root to contain
   files prepared by something else.
3. The handoff between them is explicit: an export under configured export
   roots (high risk, approval required) or a human copy. There is no silent
   channel.
4. Safety lives in the servers (policy + approval state machines), so the
   skill never has to be trusted with a bypass — it only has to *know when to
   stop*.

## Why a skill at all?

Without the skill, a capable agent with both MCP servers connected will
typically:

- slice against a failing `cura_profile_verify`,
- print without showing you the G-code estimate,
- call `moonraker_print_start` the moment you say "yes", without presenting
  the approval prompt,
- treat `moonraker_emergency_stop` and `moonraker_turn_off_heaters` as
  interchangeable.

The skill encodes the correct order — import → inspect → resolve/verify →
slice → G-code review → **human checkpoint** → transfer → confirm → print →
monitor — and the rules that make each gate meaningful.

## Data flow, step by step

| Step | Tool | Output |
| --- | --- | --- |
| import | `cura_artifact_import` | `artifact_id` (stable, content-hash) |
| inspect | `cura_mesh_inspect` | bounds/volume/watertightness |
| repair | `cura_mesh_transform` / `offset` / `remesh` / `boolean` / `merge` / `decimate` | new `artifact_id` |
| profile | `cura_profile_resolve` / `cura_profile_verify` | merged settings map; zero errors required |
| slice | `cura_slice` + `cura_slice_wait` | G-code `artifact_id` + job record |
| review | `cura_gcode_inspect` / `cura_gcode_verify` / `cura_gcode_prepare` | go/no-go + possibly a new artifact |
| transfer | `cura_artifact_export` or user copy → gcodes root | `moonraker_file_metadata` match |
| print | `moonraker_print_start` (double-confirmed) | print job; monitor with status/temps/camera |

## Approval state

Both servers persist pending approvals outside their binaries (under the
workspace/state dirs) so a prepared action can be approved from a second
terminal (`mcp-moonraker approve <id>`) or recovered after a restart
(`*_pending_approvals`). Approvals are single-use, expiring (default
TTL 120 s), and replay only the stored tool + arguments.

## Design principles for the skill itself

- **Progressive disclosure** — SKILL.md is the short version; deep detail
  lives in `references/` and loads only when needed.
- **No magic** — every step names the exact tool; the agent never has to
  guess what "check the profile" means.
- **The human is the gate** — the skill never authorizes itself past a
  destructive action, even when the human said "go ahead" three messages
  ago.
- **Honest hand-offs** — where the servers cannot do something (no upload
  tool), the skill says so and names the legitimate alternatives instead of
  improvising.
