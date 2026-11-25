# Architecture

`3d-auto-fabrik` is a skill, not a program. It carries no runtime of its own —
it is the load-bearing knowledge between three MCP servers and the agent that
drives them.

## The repositories

```text
repos/
├── skill-3d-auto-fabrik   this skill (the orchestrator)
├── mcp-orca               preferred slicing server (OrcaSlicer, mesh, G-code)
├── mcp-cura               fallback slicing server (CuraEngine, mesh, G-code)
└── mcp-moonraker          the printer server (Klipper via Moonraker)
```

The servers are deliberately independent of each other and of this skill: each
works without this skill, and this skill is useless without a slicer and a
printer server.

## Trust boundaries

```text
┌──────────────────────────────┐      ┌──────────────────────────────┐
│  mcp-orca  (preferred)       │      │        mcp-moonraker         │
│  or mcp-cura (fallback)      │      │                              │
│                              │      │  Moonraker HTTP API          │
│  STL/OBJ/3MF ──► import      │      │      └► state, temps, camera │
│      ──► mesh inspect/fix    │      │      └► heaters, fans, motion│
│      ──► profile resolve     │      │      └► print control, queue │
│      ──► slice               │      │                              │
│      ──► G-code review       │      │  host admin (off by default) │
│                              │      │  raw G-code (off by default) │
│  workspace:                  │      │                              │
│  ~/.local/share/mcp-orca     │      │  safety policy: read-only?   │
│  ~/.local/share/mcp-cura     │      │  temp caps, approval mode    │
│  content-addressed           │      │                              │
└──────────────┬───────────────┘      └──────────────▲───────────────┘
               │                                     │
               │   G-code artifact                   │  gcodes root
               └──────── approval-gated handoff ─────┘
               (*_artifact_export, or the user copies)
```

Facts that follow:

1. **Neither slicer contacts the printer.** Their outputs are files in their
   own content-addressed workspaces.
2. **mcp-moonraker never slices.** It trusts the `gcodes` root to contain
   files prepared by something else.
3. **Artifact ids do not cross servers.** An `art_…` id is meaningful only to
   the server that created it. Switching engines means re-importing the model
   and restarting the pipeline.
4. The handoff between slicer and printer is explicit: an export under
   configured export roots (approval required) or a human copy. There is no
   silent channel.
5. Safety lives in the servers (policy + approval state machines), so the
   skill never has to be trusted with a bypass — it only has to *know when to
   stop*.

## Engine selection

The skill prefers mcp-orca. It falls back to mcp-cura when Orca is not
installed, not running, or has no engine configured. The choice is made once,
before import, and reported to the user.

| Concern | mcp-orca | mcp-cura |
| --- | --- | --- |
| Presets | printer + filament + process native `.json` | definition + quality + material + variant + intent |
| Profile verify | none; inspect the final G-code | `cura_profile_verify` before slicing |
| Mesh repair | transform + merge | transform + merge + boolean/offset/remesh/decimate |
| G-code review | `orca_gcode_inspect` + text review | inspect + verify + prepare |
| Export approval | pending request → decide → retry | prepare → phrase → confirm |

Full matrix and fallback rules:
[../skills/3d-auto-fabrik/references/engine-selection.md](../skills/3d-auto-fabrik/references/engine-selection.md).

## Why a skill at all?

Without the skill, a capable agent with the MCP servers connected will
typically:

- slice against a failing Cura profile, or with an Orca engine that is not
  configured,
- print without showing you the G-code estimate,
- call `moonraker_print_start` the moment you say "yes", without presenting
  the approval prompt,
- treat `moonraker_emergency_stop` and `moonraker_turn_off_heaters` as
  interchangeable,
- mix Orca and Cura artifact ids and wonder why nothing resolves.

The skill encodes the correct order — choose engine → import → inspect →
resolve → slice → G-code review → **human checkpoint** → transfer → confirm →
print → monitor — and the rules that make each gate meaningful.

## Data flow, step by step

| Step | mcp-orca | mcp-cura | Output |
| --- | --- | --- | --- |
| choose | `orca_doctor` / `orca_engine_info` | `mcp-cura doctor` | engine name, reported to user |
| import | `orca_artifact_import` | `cura_artifact_import` | `artifact_id` (stable, content-hash) |
| inspect | `orca_mesh_inspect` | `cura_mesh_inspect` | bounds/volume/watertightness |
| repair | `orca_mesh_transform` / `merge` | transform/offset/remesh/boolean/merge/decimate | new `artifact_id` |
| profile | `orca_profile_resolve` | `cura_profile_resolve` / `verify` | selections + warnings; Cura needs zero errors |
| slice | `orca_slice` + `status/wait` | `cura_slice` + `status/wait` | G-code `artifact_id` + job record |
| review | `orca_gcode_inspect` + `read_text` | `cura_gcode_inspect` / `verify` / `prepare` | go/no-go + possibly a new artifact |
| transfer | G-code bytes → `moonraker_file_upload` | same | `moonraker_file_verify` (`verified: true`) + `moonraker_file_metadata` match |
| preflight | `moonraker_print_preflight` | same | `ready_to_prepare_start`, blocking reasons |
| print | `moonraker_print_start` (double-confirmed) | same | print job; monitor status/temps/camera |

## Approval state

Each server persists pending approvals outside its binary (under its
workspace/state dir), so a prepared action can be approved from a second
terminal or recovered after a restart (`*_pending_approvals`). Approvals are
single-use and expiring (default TTL 120 s).

The protocols differ:

- **mcp-orca** stores the request and fails the call. Decide with
  `orca_approval_decide` (in-band/both) or `mcp-orca approvals approve <id>`
  (out-of-band), then retry the identical call.
- **mcp-cura** and **mcp-moonraker** return an id and a phrase; the agent
  completes with `*_confirm_action` after the human approves.

Neither protocol lets the agent change the prepared action at confirmation
time.

## Design principles for the skill itself

- **Progressive disclosure** — SKILL.md is the short version; deep detail
  lives in `references/` and loads only when needed.
- **No magic** — every step names the exact tool; the agent never has to
  guess what "check the profile" means. Tools and arguments come from the
  generated catalogs, never from memory.
- **One engine per job** — fallback is a decision, not a drift.
- **The human is the gate** — the skill never authorizes itself past a
  destructive action, even when the human said "go ahead" three messages
  ago.
- **Honest hand-offs** — where a server cannot do something (no Orca G-code
  verify, no upload tool exposed in the session), the skill says so and stops
  instead of improvising a tool, path or result.
