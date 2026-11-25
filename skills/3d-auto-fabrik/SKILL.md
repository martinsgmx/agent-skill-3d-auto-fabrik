---
name: 3d-auto-fabrik
description: >-
  Orchestrates mcp-orca (preferred) or mcp-cura — the only slicing tools this
  skill uses — and mcp-moonraker for supervised Klipper/Moonraker printing:
  URL/ZIP model bundles and model-file discovery, a unique per-job workspace,
  printer and material configuration seeded from live MCP settings, mesh
  import and inspection, profile resolution, slicing, ready-made G-code
  validation and review, Moonraker G-code upload into the printer's gcodes
  root, file verification, print preflight, job queue, print start, live
  monitoring and pause/resume/cancel — always behind the servers' policy and
  approval gates.
  Use this skill whenever the user mentions slicing, 3D printing,
  STL/3MF/OBJ/AMF files, model download URLs or ZIPs, OrcaSlicer, CuraEngine,
  Klipper or Moonraker — even if they never name these MCP servers — and
  whenever the user asks to prepare, verify, send or supervise a print job.
  Do not use it for general CAD authoring or for editing Klipper
  firmware/printer configuration itself.
license: MIT
compatibility: >-
  Requires mcp-moonraker and at least one slicing server: mcp-orca (preferred)
  or mcp-cura (fallback). Slicing also needs OrcaSlicer or CuraEngine; printing
  needs a reachable Klipper/Moonraker host. Mesh inspection, profile review
  and slicing work without printer access.
metadata:
  author: skill-3d-auto-fabrik contributors
  version: "0.2.5"
---

# 3d-auto-fabrik

One pipeline, two interchangeable slicer adapters, one printer server:

- **mcp-orca** (preferred) — OrcaSlicer presets, mesh inspect/transform/merge,
  background slice jobs, G-code inspection.
- **mcp-cura** (fallback) — CuraEngine definitions/quality profiles, richer
  mesh repair, G-code verify/prepare.
- **mcp-moonraker** — Klipper state, temperatures, files, print control.

The slicers never contact the printer; mcp-moonraker never slices. This skill
is the glue. The hand-off is `moonraker_file_upload` into the printer's
`gcodes` root, followed by verification — never a silent copy or a made-up
transfer. Approval gates stay where the servers put them.

## Non-negotiable rules — read before touching hardware

These rules exist because a 3D printer is a heater, a motor and a sharp
nozzle. The friction is the point.

1. **Never confirm a prepared action on the user's behalf.** Every slicer
   export/delete and every destructive Moonraker action returns an approval
   prompt first. Present it clearly and wait. Only after the user explicitly
   approves — in chat, or by running the server's out-of-band approval
   command — may you complete the action. Never invent, reuse or paraphrase
   approval ids or confirmation phrases.
2. **Never skip verification to be helpful.** Review the G-code before any
   print, `moonraker_verify_connection` before any printer action, and
   `moonraker_file_verify` + `moonraker_files_list` +
   `moonraker_file_metadata` after any transfer.
3. **`moonraker_emergency_stop` is the only un-gated lever.** Use it only when
   something is physically going wrong _right now_ (smoke, grinding, nozzle
   dragging through the part, axes colliding). For "stop heating" outside an
   emergency, use `moonraker_turn_off_heaters` — reversible and un-gated.
4. **Stay inside the local safety policy.** Temperature caps, read-only mode,
   export roots, raw G-code and host administration are set by the user on
   purpose. If a tool refuses, relay the refusal and its reason. Do not
   rephrase the call, enable the flag, or find another tool that does the
   same thing.
5. **When in doubt, stop and ask.** A paused printer wastes a little
   electricity; a wrong print wastes hours and filament; a bypassed gate can
   burn a house down. The user is always reachable — ask.
6. **Slice only with mcp-orca or mcp-cura.** A slice exists only when
   `orca_slice` or `cura_slice` returns a `job_*` id. Never hand-write G-code,
   never treat a text edit as a slice, and never invent a time or filament
   estimate when no slice completed.
7. **Send G-code to the printer only through Moonraker.** The agent-side path
   is `moonraker_file_upload` into the `gcodes` root, then
   `moonraker_file_verify` and `moonraker_print_preflight`. A raw HTTP call, a
   silent copy into the gcodes root, or a claimed transfer without a verified
   file is not an acceptable substitute.
8. **Use only tools that actually exist.** Call only tool names and arguments
   listed in the generated catalogs below, and only tools exposed in this
   session. Never invent a tool, an argument, an id, a path, a URL, a policy
   value or a tool result. Quote tool output; if a tool is missing or fails,
   say so and stop instead of substituting a plausible-looking action. See
   [references/tool-discipline.md](references/tool-discipline.md).

## Choose the slicer, once per job

Pick the engine before importing. Artifact ids are local to one server; do not
mix servers mid-job.

1. Try **mcp-orca** first: run `mcp-orca doctor` (or `orca_doctor`) and
   `orca_engine_info`. It is usable when the engine probe reports both
   `available: true` (binary or image found) and
   `slice_command_configured: true` (`engine.preset = "orca"` or a
   `slice_command`). The doctor's overall `ok` can be true while the engine
   entry is `"ok": false`; and `available: true` with
   `slice_command_configured: false` still cannot slice. Read the engine
   entry, not just the exit code.
2. If mcp-orca is missing, fails to start, or has no engine configured, run
   `mcp-cura doctor` and use **mcp-cura** for the whole job. Say which engine
   you chose in one line; do not make the user re-ask.
3. If neither is usable, stop and point at
   [references/troubleshooting.md](references/troubleshooting.md). Do not
   install packages or edit configs to force a check to pass.
4. If Orca lacks a capability the job needs (boolean/offset/remesh/decimate),
   say so and offer Cura. Switching engines means re-importing the model into
   the other server and restarting at Stage 1 — never pass one server's
   `artifact_id` to the other.
5. If the user names a **Cura profile or the Cura engine** but no mcp-cura
   tools are available, do not silently substitute. Say Cura is unavailable,
   search the active slicer's presets for the same or closest name, and show
   exact ids/paths. Require explicit confirmation before treating a
   Cura-named profile as an Orca preset — a name match is not consent.

Details, capability matrix, the Cura-name dialogue and fallback rules:
[references/engine-selection.md](references/engine-selection.md).

## Job workspace and input discovery

Every job gets one unique workspace. It is the only place where downloaded
archives, extracted models and job notes live; never reuse a name or mix two
jobs. Full rules: [references/job-workspace.md](references/job-workspace.md).

1. If the user gives an **http(s) URL to a ZIP**, download it (512 MiB cap),
   extract into a fresh `job_<UTC-timestamp>_<random-hex>` directory under a
   platform-neutral temp root (`${TMPDIR:-/tmp}/3d-auto-fabrik/` — never a
   client-specific path), and reject zip-slip, symlinks and nested-archive
   auto-recursion.
2. Otherwise, scan `model_downloaded/files/` recursively first (configurable;
   do not create it) — including when the user gave a folder rather than one
   file. It may be loosely organised; the goal is to find models. An explicit
   single file the user names is checked directly but still listed for
   confirmation.
3. Recognise `.stl`, `.3mf`, `.obj`, `.amf`. A `.3mf` is **one** model
   artifact (it is already a ZIP); never unzip it ourselves. List other files
   as assets but do not import them; a found `.gcode` goes to the G-code-only
   branch below.
4. Always **show what was found and ask the user which file(s)** to use.
   Never auto-pick by name or timestamp. Ask whether multiple models are
   separate bed objects or one merged artifact (merge is a triangle soup).
5. Import discovered bytes with the base64 `data` channel; never widen
   `import_roots` for one job. Keep the workspace until the job ends and ask
   before deleting it — including after cancel or abort.

## Preflight gate — before every mutating stage

Run this gate once per session and **repeat it at the start of every mutating
stage** (import, slice, queue, print). Produce a readiness table; a red row
blocks mutations, not read-only work.

| Check         | Tool                                                                                   | Green means                                                                         |
| ------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Slicer health | `mcp-orca doctor` or `mcp-cura doctor`                                                 | server up; read the engine entry, not just overall `ok`                             |
| Engine usable | `orca_engine_info` / `cura_engine_info`                                                | `available: true` **and** `slice_command_configured: true` (or the Cura equivalent) |
| Policies      | `orca_policy_info` / `cura_policy_info`, `moonraker_policy_info`                       | caps, approval mode and read-only switches known                                    |
| Printer       | `moonraker_verify_connection`, `moonraker_server_info`, `moonraker_config` (read-only) | connected; Klipper `ready`; facts for printer identity                              |
| Queue         | `moonraker_job_queue_status`                                                           | state and existing jobs known (a paused queue never auto-starts)                    |
| Presets       | `orca_profile_list` / `cura_profile_list` + user config                                | printer + filament + process (or Cura essentials) resolvable                        |

Then settle the plan with the user: **which printer, which material, which
nozzle, which quality/process preset, which file, how many copies, where on
the bed.** Use the live MCP facts and the user config below; do not guess.

If any row is red: report the tool's own words, stop all mutations, and let
read-only work (mesh inspect, profile review) continue. Never install a
package, edit a config or retry with altered arguments to make a row green.

A missing entry in `*_profile_list` is not proof a preset is unusable: the
list is a bounded index. Resolve an exact path before concluding a preset is
absent — see
[references/printer-materials.md](references/printer-materials.md).

## Printer, material and profile configuration

Load [references/printer-materials.md](references/printer-materials.md) when
choosing a printer or material. Principles, not a hard-coded catalog:

- The **live MCP config is the source of truth**: `orca_server_info` /
  `orca_doctor`, `orca_profile_list`, both `*_policy_info`, and
  `moonraker_config` / `moonraker_server_info` supply preset paths, hostname
  and config facts. Read them every preflight.
- User preferences live in `~/.config/3d-auto-fabrik/config.yaml` with an
  optional `./3d-auto-fabrik.yaml` override: labels mapped to **exact** preset
  ids, temp root, size cap. No tokens or secrets — those stay in MCP env.
- Discovery order: MCP-indexed presets → ask the user for a preset directory
  (read-only) → workspace custom profiles/overrides. Never edit slicer config
  or `printer.cfg` to force a check to pass.
- Every material label (PLA, ABS, PLA silk, PETG, …) must be mapped by the
  user to a concrete filament/material preset. Never fuzzy-match a name; if
  unmapped, ask. Shipped values are examples in the reference only.
- Onboarding is optional and only when the user asks; it pre-fills that user
  config from live MCP facts and writes nothing else.

## The pipeline

Work stage by stage. Report briefly after each stage and pause for the user
whenever a gate requires it.

**Stage 0 — Plan.** Summarize the job in one paragraph and get the go-ahead.
Use this template so every confirmation covers the same facts:

```text
Plan confirmation — <job id or workspace path>
Files / models:      <exact files; artifact ids recorded after import>
Engine:              <mcp-orca | mcp-cura> — why this one
Printer identity:    <from moonraker_server_info + user label>
Material mapping:    <user label → exact preset id/path>
Profiles:            <printer / filament / process or Cura equivalents>
Copies / placement:  <count and position on the bed>
Transfer mode:       <moonraker_file_upload to gcodes | explicit user override>
Print mode:          <direct print | job queue>
```

Do not start the first mutating stage until the user confirms this plan.

**Stage 1 — Import.**

- First discover and choose the file(s) in the job workspace as described
  above. Discovered bytes go in through base64 `data`; a user-named path may
  use `path` only when it is already under an import root.
- Orca: `orca_artifact_import` with an absolute path under
  `workspace.import_roots`, or with base64 `data` plus `name`. **The default
  import roots are empty**, so path imports are disabled until the user
  configures them; `data` is the sanctioned channel for client-supplied bytes
  and needs no policy change.
- Cura: `cura_artifact_import` with a path under its default roots
  (`~/Downloads`, `~/Documents`, `~/Desktop`, `~/models`) or base64 `data`.

If a path import is refused, re-import the same bytes via `data`
(content-addressing returns the same artifact id) instead of stripping the
job down to "I can't help". Record the returned `artifact_id` — every later
step references it.

Then call `orca_artifact_get` / `cura_artifact_get` and assert `kind` and
`format` match the request **before Stage 2**. If the artifact is
`kind: "other"` or otherwise unexpected, report the metadata verbatim and do
not run mesh tools on it. Re-import the original bytes with explicit
`kind`/`format`; if content-addressing returns the same id, treat it as an
upstream classification issue and stop/ask. A harmless header change is a
last-resort diagnostic only — never present it as a geometry repair.

**Stage 2 — Inspect & repair.** Always `orca_mesh_inspect` /
`cura_mesh_inspect` first (bounds in mm, triangle count, watertightness,
volume, degenerate triangles). Then:

| Need                            | mcp-orca                                                  | mcp-cura                                                     |
| ------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------ |
| orient / place / scale / mirror | `orca_mesh_transform` (scale/mirror → rotate → translate) | `cura_mesh_transform` (+ `center_on_bed`)                    |
| combine parts                   | `orca_mesh_merge` (triangle soup)                         | `cura_mesh_merge`, `cura_mesh_boolean`                       |
| clean / thicken / simplify      | not available                                             | `cura_mesh_remesh`, `cura_mesh_offset`, `cura_mesh_decimate` |

Inspect again after every repair and quote the numbers. Mesh writes are
policy-gated but not approval-gated; still, show the user what changed. If
Orca cannot do a needed repair, do not pretend a merge is a boolean — offer
Cura and restart at Stage 1.

**Stage 3 — Resolve the profile.**

- Orca needs three native `.json` presets: **printer + filament + process**
  (no invented defaults). Use `orca_profile_list` to find them, then
  `orca_profile_resolve` with `printer`, `filament`, `process`, and optional
  `overrides`. Check `resolution[]` sources and read every warning. A
  `settings_complete: false` for native presets is normal: Orca resolves
  those files by reference at slice time. There is no `orca_profile_verify`;
  the final G-code is the verification surface (Stage 5). If a role is
  omitted, `orca_slice` uses defaults saved earlier through
  `orca_config_setup` — confirm them in the plan, never assume them.
  Repeatable overrides belong in a workspace profile: `orca_profile_create` with
  `base_profile` + `settings`.
- Cura: `cura_profile_list` → `cura_profile_resolve` (definition + quality +
  material + variant + intent) → `cura_profile_verify`. Errors must be zero
  before slicing.

**Stage 4 — Slice.**

- Orca: `orca_slice(model_artifact_ids=[…], printer, filament, process,
overrides?, profiles?, name, wait=true, wait_timeout_secs)`. Slicing fails
  clearly when no engine invocation is configured. Respect
  `max_concurrent_jobs` (default 2); poll `orca_slice_status`, or
  `orca_slice_wait` for short jobs. `orca_slice_cancel` is for queued/running
  jobs only.
- Cura: `cura_slice(model_artifact_ids=[…], definition, quality, material,
variant, intent, overrides?, name, wait=true, wait_timeout_secs)`. Same job
  rules; poll `cura_slice_status` / `cura_slice_wait` / `cura_slice_cancel`.

If a slice fails, quote the actual engine error from the job status — never
guess at a cause. Record the `job_*` id and terminal status: without them
there is no slice and no time/filament estimate to report. Writing G-code by
hand, or presenting an edited file as sliced output, is not a slice.

**Stage 5 — G-code review.** This is the last cheap chance to abort.

- Orca: `orca_gcode_inspect` reports time, filament, layers, Z range and
  maximum nozzle/bed temperatures, but **does not detect dangerous commands**.
  Read the header and footer with `orca_artifact_read_text` (first ~200 and
  last ~120 lines). Confirm:
  - max temperatures are within `moonraker_policy_info` caps and the
    material's limits;
  - the end sequence turns heaters off (`M104 S0` / `M140 S0`), parks/lifts,
    and disables steppers (`M84`);
  - no unexpected `M112`, `M502`, `M500`, mid-file `G28`, or raw commands the
    profile should not contain.
    If the end sequence is wrong or dangerous commands are present, re-slice
    with a corrected process preset. mcp-orca has no G-code rewrite tool — do
    not hand-edit the artifact.
- Cura: `cura_gcode_inspect` + `cura_gcode_verify`. If shutdown or steppers
  are missing, `cura_gcode_prepare` creates a _new_ artifact; carry the new
  id forward. Dangerous commands mean re-slice, never a hand edit.
- **Cross-check the numbers.** Compare `orca_gcode_inspect` /
  `cura_gcode_inspect` with the G-code's own header/config summary (`total
  layer number`, `total layers count`, `filament used [mm]`, temperatures) and,
  after transfer, with `moonraker_file_verify` and
  `moonraker_file_metadata`. Report discrepancies explicitly; do not treat one
  source as authoritative for informational
  values. Safety fields — max temperatures against caps, `M112` / `M500` /
  `M502` / mid-file `G28`, heater-off and stepper-disable in the footer —
  remain gating. A numbers-only mismatch is reported, not silently ignored
  and not a blocker by itself.

Then **show the user the summary** and get explicit confirmation before Stage 6:

```text
Stage 5 review — <gcode artifact id>
Engine / slice job:   <engine, job_* id>
Time / filament:      <estimate; mm and g>
Layers / Z range:     <inspect value vs header summary value>
Max nozzle / bed:     <°C; vs policy caps and material limits>
Move bounds:          <where reported, vs build volume; else "not reported">
Dangerous commands:   <none | list of commands found>
End sequence:         <heaters off, park/lift, M84 — PASS/FAIL>
Discrepancies:        <inspect vs summary vs Moonraker metadata, or "none">
Verdict:              <PASS / FAIL with tool evidence>
Next gated action:    <transfer method and approval to expect>
```

Do not proceed while the verdict is FAIL.

**Branch — the user supplied ready-made G-code.** Skip Stages 2–4 and do not
pretend the file was sliced. Import it as `kind: "gcode"`, then run the Stage 5
review plus a printer-compatibility check: temperature maxima against
`moonraker_policy_info` caps and the selected material's limits; move bounds
against the selected printer profile's build volume; heater-off and
stepper-disable in the footer; no dangerous commands; and any macro or
firmware requirement visible in read-only `moonraker_config` /
`moonraker_list_macros`. Report a clear PASS/FAIL with the tool evidence.
Then **stop** — no queue, no transfer, no print unless the user asks in a
separate turn. A failed check is reported verbatim; with no mesh there is no
"just re-slice" fix, and the G-code is never hand-edited.

**Stage 6 — Upload the G-code with Moonraker.** The sliced G-code must land in
the printer's `gcodes` root. The agent-side transfer is
`moonraker_file_upload`; no slicer contacts the printer. Do not substitute a
raw HTTP endpoint, an export-root hand-off or a direct filesystem copy unless
the upload tool is unavailable and the user explicitly chooses that fallback
after you say so. Detail: [references/pipeline.md](references/pipeline.md).

1. `moonraker_policy_info` must allow mutations. If an upload is refused,
   relay the refusal and stop — do not work around the policy.
2. Read the artifact's `sha256` and `bytes` with `orca_artifact_get` /
   `cura_artifact_get`; these are the expected values for verification. Get
   the exact bytes from a real copy: `cura_artifact_get` reports `blob_path`;
   Orca artifacts can be exported with `orca_artifact_export` to a configured
   export root (approval-gated). If no export root is configured, ask the
   user to configure one; never edit the server config yourself. If only text
   is available, use `*_artifact_read_text` and require `truncated: false`.
   Encode the bytes with your platform's base64 encoder (`base64 -w0` or
   equivalent). If none is available, ask the user. Never type or reconstruct
   base64 by hand, and never guess a blob path.
3. Pick an unused filename (`moonraker_files_list`, root `gcodes`) and call
   `moonraker_file_upload` with `filename`, `data_base64` and
   `root="gcodes"`; keep `overwrite=false`. Overwrite is destructive and
   needs a human decision via `moonraker_confirm_action`.
4. Verify with `moonraker_file_verify(filename, expected_sha256,
   expected_size)`; require `verified: true`. Then confirm with
   `moonraker_files_list` (root `gcodes`) and `moonraker_file_metadata` —
   estimated time and filament should match the slicer output. Report a
   numbers-only mismatch; never claim a transfer without these checks.

**Stage 7 — Queue or print.** Choose with the user; both paths need the same
readiness checks.

- Direct print: `moonraker_print_preflight` first — a read-only check of
  Klippy state, active job, queue, temperatures, file existence/metadata and
  policy caps; it returns `ready_to_prepare_start` and blocking reasons.
  Then `moonraker_printer_status` shows Klipper ready and idle, not shut down
  or busy; `moonraker_temperatures` shows sane ambient readings.
  Bed is clear, correct plate, correct material loaded, door closed — ask the
  user; you cannot see it. The user confirms the exact filename.
  `moonraker_print_start` prepares a high-risk action; relay the approval
  prompt and wait for approval, then `moonraker_confirm_action` with the
  phrase and `acknowledge=true`.
- Optional queue: `moonraker_job_queue_status` first, then
  `moonraker_job_queue_add` with the exact filename in the `gcodes` root. A
  paused queue stays paused — `moonraker_job_queue_start` only after explicit
  confirmation. Show the queue again so the user sees what is waiting.

Use this print-start template for a direct print or when a queued job loads:

```text
Print start
File on gcodes root:   <exact filename from moonraker_files_list>
Verified:              <moonraker_file_verify verified, sha256/size match>
Preflight:             <ready_to_prepare_start and any blocking reasons>
Metadata match:        <time/filament vs slicer output>
Printer state:         <ready and idle; not shut down or busy>
Temperatures:          <sane ambient readings>
Physical checks:       <bed clear, correct plate, material, door — user confirms>
Approval:              <apr_* id, phrase and TTL from the prepare response>
Await:                 the phrase in chat or out-of-band approval, then
                       moonraker_confirm_action(id, phrase, acknowledge=true)
```

During the print (or when a queued job loads): poll `moonraker_printer_status` and
`moonraker_temperatures`; use `moonraker_camera_snapshot` for a visual check
when something seems off; `moonraker_gcode_history` when commands fail. To
hold the print for inspection use `moonraker_print_pause` → inspect →
`moonraker_print_resume`. To abort, `moonraker_print_cancel` (high risk,
double confirmation) — only when the user asks. Afterwards,
`moonraker_print_history` records the outcome.

**Post-print and cleanup.** Heaters should be off (the end sequence does it —
verify with `moonraker_temperatures`). Remind the user to clear the plate. If
the user wants artifacts cleaned up, list them (`orca_artifact_list` /
`cura_artifact_list`) and only delete with explicit confirmation —
`*_artifact_delete` is high risk. Offer the same for the per-job workspace;
delete it only after explicit confirmation, and offer it on cancel/abort too.

Keep an audit trail: include the ids you touched (`art_*`, `job_*`, `apr_*`)
and exact filenames in each stage report and in the final summary. Remove any
temporary transfer files or localhost helper server immediately after use;
keep the job workspace until the user confirms deletion.

## Approvals in one breath

One prepared action = one single-use approval with a short TTL (default
120 s). The stored tool and arguments are what execute; arguments supplied
later are decorative.

| Server        | Prepare                                         | Decide                                                                     | Then                                                        |
| ------------- | ----------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------- |
| mcp-orca      | first gated call returns `apr_…`                | `orca_approval_decide` (in-band/both) or `mcp-orca approvals approve <id>` | retry the **identical** call once                           |
| mcp-cura      | first gated call returns `approval_id` + phrase | user reads/approves in chat, or `mcp-cura approve <id>`                    | `cura_confirm_action` with phrase + `acknowledge=true`      |
| mcp-moonraker | first gated call returns `approval_id` + phrase | user reads/approves in chat, or `mcp-moonraker approve <id>`               | `moonraker_confirm_action` with phrase + `acknowledge=true` |

`*_pending_approvals` re-lists what is waiting; `moonraker_cancel_approval` /
`mcp-orca approvals deny <id>` / `mcp-cura deny <id>` void an action before it
runs. Full protocol: [references/safety-approvals.md](references/safety-approvals.md).

## Quick reference — where to read more

- [references/setup.md](references/setup.md) — environment check, MCP verification, and explicitly-confirmed defaults
- [references/engine-selection.md](references/engine-selection.md) — Orca vs Cura, fallback rules, artifact transfer
- [references/job-workspace.md](references/job-workspace.md) — URL/ZIP download, unique workspace, model discovery, archive safety, cleanup
- [references/printer-materials.md](references/printer-materials.md) — live MCP config, printer/material mapping, preset discovery, onboarding
- [references/pipeline.md](references/pipeline.md) — expanded stage walkthrough with an example dialog
- [references/mcp-orca-tools.md](references/mcp-orca-tools.md) — all mcp-orca tools: risk, gate, arguments
- [references/mcp-cura-tools.md](references/mcp-cura-tools.md) — all mcp-cura tools likewise
- [references/mcp-moonraker-tools.md](references/mcp-moonraker-tools.md) — all mcp-moonraker tools likewise
- [references/safety-approvals.md](references/safety-approvals.md) — approval modes, refusal rules, emergency handling
- [references/tool-discipline.md](references/tool-discipline.md) — use only cataloged tools; no invented ids, paths or results
- [references/troubleshooting.md](references/troubleshooting.md) — doctor output, common failures, fixes
- [scripts/check-setup.sh](scripts/check-setup.sh) — verify the servers are installed and reachable

Installation and per-platform MCP/skill registration live in the repository
docs (`docs/platforms.md`), not in this skill — load them when the user asks
about setup.

## When not to use this skill

Drafting or repairing CAD/STL geometry by hand (use a modeling tool), editing
`printer.cfg` or Klipper includes (host admin and config-write are off by
default — and should stay off), or anything involving host reboots, firmware
restarts or raw G-code that the user has not explicitly enabled. Say so and
stop.
