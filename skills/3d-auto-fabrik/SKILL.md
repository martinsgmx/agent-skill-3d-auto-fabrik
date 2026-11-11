---
name: 3d-auto-fabrik
description: >-
  Orchestrates the mcp-cura and mcp-moonraker MCP servers so an agent can take a
  3D model from a mesh file to a supervised Klipper/Moonraker print: mesh
  inspection and repair, CuraEngine profile resolution and slicing, G-code
  safety verification, transfer to the printer, print start, live monitoring,
  pause/resume/cancel and job-queue management — always behind the servers'
  risk and approval gates. Use this skill whenever the user mentions slicing,
  3D printing, STL/3MF slicing, CuraEngine, Klipper or Moonraker — even if they
  never name these MCP servers — and whenever the user asks to prepare, verify,
  send or supervise a print job. Do not use it for general CAD authoring or for
  editing Klipper firmware/printer configuration itself.
license: MIT
compatibility: >-
  Requires the mcp-cura and mcp-moonraker MCP servers (Rust binaries on PATH),
  CuraEngine for slicing, and a reachable Klipper/Moonraker host for printing.
  Mesh inspection, G-code review and slicing work without printer access.
metadata:
  author: skill-3d-auto-fabrik contributors
  version: "0.1.0"
---

# 3d-auto-fabrik

Orchestrator for **mcp-cura** (mesh → slice → G-code) and **mcp-moonraker**
(printer state → print). The two servers deliberately do not know about each
other: mcp-cura never contacts the printer, and mcp-moonraker never slices.
This skill is the glue. Files move between them only through an explicit,
approval-gated handoff.

## Non-negotiable rules — read before touching hardware

These rules exist because a 3D printer is a heater, a motor and a sharp
nozzle. The friction is the point.

1. **Never confirm a prepared high-risk action on the user's behalf.**
   `moonraker_print_start`, `moonraker_print_cancel`, `moonraker_run_macro`,
   `cura_artifact_export`, `moonraker_file_delete` and friends return an
   approval prompt first. Your job is to present that prompt, clearly and
   honestly, and wait. Only after the user explicitly approves (in chat, or by
   running `mcp-moonraker approve <id>` / `mcp-cura approve <id>` out of band)
   may you call the matching `*_confirm_action` tool. Never invent, reuse or
   paraphrase approval ids or confirmation phrases.
2. **Never skip verification to be helpful.** `cura_gcode_verify` before any
   print, `moonraker_verify_connection` before any printer action,
   `moonraker_files_list` + `moonraker_file_metadata` after any transfer.
3. **`moonraker_emergency_stop` is the only un-gated lever.** Use it only when
   something is physically going wrong *right now* (smoke, grinding, nozzle
   dragging through the part, axes colliding). For "stop heating" outside an
   emergency, use `moonraker_turn_off_heaters` — reversible and un-gated.
4. **Stay inside the local safety policy.** Temperature caps, read-only mode,
   `allow_raw_gcode`, `allow_host_admin` are set by the user on purpose. If a
   tool refuses, relay the refusal and its reason. Do not rephrase the call,
   enable the flag, or find another tool that does the same thing.
5. **When in doubt, stop and ask.** A paused printer wastes a little
   electricity; a wrong print wastes hours and filament; a bypassed gate can
   burn a house down. The user is always reachable — ask.

## Preflight — every session that touches hardware

1. `mcp-cura doctor` and `mcp-moonraker doctor` (local, read-only diagnostics).
2. `moonraker_verify_connection` — connected? latency? Klipper ready, busy or
   shut down?
3. `cura_policy_info` and `moonraker_policy_info` — learn the active limits
   (temperature caps, approval mode, read-only switches) before planning a
   mutation.
4. `moonraker_server_info` — confirm Klipper is `ready`, not `shutdown` or busy
   with another job.
5. Settle the plan with the user: **which printer, which material, which
   nozzle, which quality, which file, how many copies, where on the bed.**
   Do not guess.

If a server is missing or won't connect, say so and point the user at
[references/troubleshooting.md](references/troubleshooting.md). Do not edit
configs, install packages, or run `--force` anything just to make a check
pass.

## The pipeline

Work stage by stage. Report briefly after each stage and pause for the user
whenever a gate requires it.

**Stage 0 — Plan.** Summarize the job in one paragraph (file, printer,
material, nozzle, profile, copies, placement). Get the go-ahead.

**Stage 1 — Import.** `cura_artifact_import` with an absolute path under the
configured import roots (`~/Downloads`, `~/Documents`, `~/Desktop`,
`~/models` by default) — or with the base64 `data` parameter for a file
outside the roots. The roots confine *filesystem paths*; the `data` path is
the server's own supported channel for client-supplied bytes, not a bypass,
and needs no policy change. If a path import is refused, re-import the same
bytes via `data` (content-addressing returns the same artifact id) instead
of stripping the job down to "I can't help". Record the returned
`artifact_id` — every later step references it.

**Stage 2 — Inspect & repair.** `cura_mesh_inspect` (bounds in mm, triangle
count, watertight, volume, degenerate triangles). Then, as needed:

- orientation / placement / scaling → `cura_mesh_transform`
  (scale → rotate → translate, then `center_on_bed`)
- non-manifold or messy surface → `cura_mesh_remesh` with a `voxel_size`, or
  `cura_mesh_offset` to swell/shrink a closed mesh
- several parts as one print → `cura_mesh_merge` (triangle soup) or
  `cura_mesh_boolean` (a true union/subtract — voxel-based)
- too many triangles → `cura_mesh_decimate` toward `target_triangles`

Inspect again after every repair and quote the numbers. Medium-risk mesh ops
are policy-gated but do not need approval; still, show the user what changed.

**Stage 3 — Resolve & verify the profile.** `cura_profile_list` to find
definitions and quality profiles, then `cura_profile_resolve`
(definition + quality + material + variant + intent). Read the warnings: Cura
expressions it cannot evaluate, hard temperature violations. Then
`cura_profile_verify` — errors must be zero before you slice. If they are
not, fix the profile (or pick another) and say why. Never slice against a
failing verify.

**Stage 4 — Slice.** `cura_slice(model_artifact_ids=[…], definition, quality,
material, variant, intent, overrides?, name, wait=true, wait_timeout_secs)`.
Respect `max_concurrent_jobs` (default 2). Poll with `cura_slice_status`;
`cura_slice_wait` for short jobs; `cura_slice_cancel` only for queued/running
jobs. If the slice fails, `cura_slice_status` carries the engine log tail —
quote the actual error.

**Stage 5 — G-code review.** On the G-code artifact returned by the slice:

- `cura_gcode_inspect` — estimated time, filament, layer count, Z range, max
  temperatures, suspicious commands.
- `cura_gcode_verify` — dangerous commands, temperatures vs. local policy,
  missing heater shutdown / stepper disable / metadata.
- If something is missing, `cura_gcode_prepare` creates a *new* artifact with
  a safe shutdown sequence (or full end sequence). When you use it, carry the
  **new** artifact id forward — the original is untouched.

Then **show the user the summary** — time, filament, hottest temperature,
verify result — and get explicit confirmation before Stage 6. This is the
last cheap chance to abort.

**Stage 6 — Transfer to the printer.** The G-code artifact must exist in the
printer's `gcodes` root. The MCP servers expose no upload tool; the supported
paths are:

- `cura_artifact_export` to an export root the printer can read (a mounted
  share/USB the printer watches), or
- the user copies the file there themselves (web UI, SCP, the share), or
- if — and only if — the user explicitly asks, the Moonraker HTTP upload
  endpoint as a clearly logged one-off.

Before touching the printer, confirm the file arrived:
`moonraker_files_list` (root `gcodes`) and `moonraker_file_metadata` —
estimated time and filament should match the Cura output.

**Stage 7 — Print.** Before `moonraker_print_start`:

- `moonraker_printer_status` shows Klipper ready and idle, not shut down or
  busy; `moonraker_temperatures` shows sane ambient readings.
- Bed is clear, correct plate, correct material loaded, door closed — ask
  the user; you cannot see it.
- The user confirms the exact filename. `moonraker_print_start` prepares a
  high-risk action; relay the approval prompt and wait for approval, then
  `moonraker_confirm_action` with the phrase and `acknowledge=true`.

During the print: poll `moonraker_printer_status` and
`moonraker_temperatures`; use `moonraker_camera_snapshot` for a visual check
when something seems off; `moonraker_gcode_history` when commands fail. To
hold the print for inspection use `moonraker_print_pause` → inspect →
`moonraker_print_resume`. To abort, `moonraker_print_cancel` (high risk,
double confirmation) — only when the user asks. Afterwards,
`moonraker_print_history` records the outcome.

**Post-print.** Heaters should be off (the end sequence does it — verify with
`moonraker_temperatures`). Remind the user to clear the plate. If the user
wants the artifacts cleaned up, list them (`cura_artifact_list`) and only
delete with explicit confirmation — `cura_artifact_delete` is high risk.

## Approvals in one breath

Approval modes (`in_band`, `out_of_band`, `both`) are configured per server in
`[approval]`. In every mode, one prepared action = one `approval_id` = a
single-use confirmation phrase with a short TTL (default 120 s). The stored
tool and arguments from the prepare call are what execute; arguments given to
`*_confirm_action` are decorative. `*_pending_approvals` re-lists what is
waiting; `moonraker_cancel_approval` / `mcp-cura deny <id>` void an action
before it runs. Full protocol: `references/safety-approvals.md`.

## Quick reference — where to read more

- [references/pipeline.md](references/pipeline.md) — expanded stage walkthrough with an example dialog
- [references/mcp-cura-tools.md](references/mcp-cura-tools.md) — all 32 mcp-cura tools: risk, gate, arguments
- [references/mcp-moonraker-tools.md](references/mcp-moonraker-tools.md) — all 49 mcp-moonraker tools likewise
- [references/safety-approvals.md](references/safety-approvals.md) — approval modes, refusal rules, emergency handling
- [references/troubleshooting.md](references/troubleshooting.md) — doctor output, common failures, fixes
- [scripts/check-setup.sh](scripts/check-setup.sh) — verify both servers are installed and reachable

Installation and per-platform MCP/skill registration live in the repository
docs (`docs/platforms.md`), not in this skill — load them when the user asks
about setup.

## When not to use this skill

Drafting or repairing CAD/STL geometry by hand (use a modeling tool), editing
`printer.cfg` or Klipper includes (host admin and config-write are off by
default — and should stay off), or anything involving host reboots, firmware
restarts or raw G-code that the user has not explicitly enabled. Say so and
stop.
