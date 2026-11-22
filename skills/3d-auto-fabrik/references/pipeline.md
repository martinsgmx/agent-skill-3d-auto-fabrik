# The mesh → print pipeline in detail

Expanded companion to SKILL.md. Load this when you are actually running a
job. Tool names are exact; risk tiers and gates are the servers' own. The
examples use mcp-orca; mcp-cura equivalents are in parentheses.

## Example dialogue (abbreviated)

> **User:** Slice ~/Downloads/bracket.stl on the Voron, PETG, 0.2 process.
> **Agent:** Orca is up with an engine configured. Importing and inspecting
> first… (`orca_artifact_import` → `artifact_id=art_01J…`; the path is refused
> because import roots are empty, so I re-imported the same bytes via `data`).
> `orca_mesh_inspect`: 12 triangles, watertight, 8000 mm³, 20 × 20 × 20 mm.
> …
> **Agent:** `orca_profile_resolve` with printer `Voron 2.4 0.4`, filament
> `Generic PETG`, process `0.20mm Standard`: all three resolve to native
> presets, no warnings. Slice complete: 1 h 42 m, 4.8 m of filament.
> `orca_gcode_inspect`: max nozzle 245 °C, bed 80 °C — under Moonraker's
> 300/120 caps. Footer has `M104 S0`, `M140 S0`, `M84`. **Shall I send it to
> the printer?**
> **User:** Yes.
> **Agent:** Exporting to the gcodes share — approval request `apr_09XY…` is
> pending. Please approve it in chat or run `mcp-orca approvals approve
> apr_09XY…`.
> **User:** Approved.
> **Agent:** Retried the identical export; file landed. `moonraker_file_metadata`
> matches (1 h 39 m vs 1 h 42 m estimate — fine). Starting the print — you'll
> get a Moonraker approval prompt:
> `apr_10AB… "print_start bracket.gcode" — approve with phrase: FRONT-…`
> **User:** Approved.
> **Agent:** `moonraker_confirm_action` → print started. I'll check in every few
> minutes; tell me if anything looks off, or say "pause".

Cura fallback sounds the same; substitute `cura_*` tools and expect a
`cura_gcode_verify` step before the checkpoint.

## Preflight gate

Before any mutation — and again at the start of import, slice, queue and
print — produce a readiness table:

- slicer doctor **and** its engine entry (`available` plus
  `slice_command_configured` for Orca; `cura_engine_info` for Cura);
- `orca_policy_info`/`cura_policy_info` and `moonraker_policy_info`;
- `moonraker_verify_connection`, `moonraker_server_info` and read-only
  `moonraker_config` for printer identity and caps;
- `moonraker_job_queue_status` (queue state, existing jobs);
- preset availability from `orca_profile_list`/`cura_profile_list` plus the
  user's label → id mapping in `~/.config/3d-auto-fabrik/config.yaml`.

Red blocks mutations, not read-only inspection. Quote the failing tool's own
words; never install, edit config or retry with altered arguments. Details:
`references/printer-materials.md`.

## Stage details and pitfalls

### Stage 1 — Import

- First create the per-job workspace and discover the input: a URL is
  downloaded and extracted into a unique directory; otherwise scan
  `model_downloaded/files/` recursively. List candidates with paths and sizes
  and ask which file(s) to use. See `references/job-workspace.md` for archive
  safety, `.3mf` handling and workspace cleanup.
- **Orca**: `orca_artifact_import` accepts `path` under
  `workspace.import_roots` or base64 `data` + `name`. Default import roots are
  **empty**; path imports are disabled until configured. Re-importing the same
  bytes returns the same id.
- **Cura**: `cura_artifact_import` accepts a path under its default roots or
  base64 `data`.
- A path outside the roots is refused. Re-import the same bytes via `data`;
  do not ask the user to widen the roots just for one job, and do not treat
  the refusal as "import is impossible".
- `kind` can hint `mesh` / `gcode` / `profile`; pass `format: "stl"` (or the
  right format) when unsure.

### Stage 2 — Inspect & repair

- Report: triangle count, bounds, watertightness, volume. If bounds exceed
  the printer's build volume, stop — propose a transform/scale or ask whether
  to split.
- Orca transform order is scale/mirror → rotate → translate. Output is binary
  STL. Orca merge concatenates triangles; it is **not** a boolean union.
- Cura has boolean/offset/remesh/decimate. If the job needs one, offer Cura
  and restart at Stage 1; do not pass an Orca id to Cura.
- Inspect again after every repair and quote the numbers.

### Stage 3 — Profile resolve

- **Orca**: `printer`, `filament`, `process` are all required. Use
  `orca_profile_list` to discover native `.json` presets, then
  `orca_profile_resolve`. Missing essentials are a hard stop; unresolved
  selections come back as warnings and must be fixed before slicing. There is
  no `orca_profile_verify` — temperature sanity is checked on the G-code.
- **Cura**: `definition` is the machine definition (e.g. `voron24_0.4`);
  quality/material/variant/intent come from `cura_profile_list`.
  `cura_profile_resolve` warns about unevaluatable Cura expressions; quote
  warnings to the user. `cura_profile_verify` must return zero errors.

### Stage 4 — Slice

- **Orca**: `orca_slice(model_artifact_ids=[…], printer, filament, process,
  overrides?, profiles?, name, wait=true, wait_timeout_secs)`. It fails
  clearly when neither `engine.preset = "orca"` nor `engine.slice_command` is
  configured. Jobs run in the background; poll `orca_slice_status`, or
  `orca_slice_wait` for short jobs. `max_concurrent_jobs` defaults to 2.
- **Cura**: `cura_slice(...)` with definition/quality/material/variant/intent.
  Same polling rules.
- On failure, quote the engine log tail from the job status. Do not invent a
  cause.

### Stage 5 — G-code review

- **Orca** has `orca_gcode_inspect` only. It reports time, filament, layers, Z
  range and maximum temperatures — **not** dangerous commands. Use
  `orca_artifact_read_text` on the first ~200 and last ~120 lines to check the
  header/footer: heater-off commands, park/lift, `M84`, and no unexpected
  `M112`/`M502`/`M500`/mid-file `G28`. If the end sequence is wrong, re-slice
  with a corrected process preset; there is no Orca prepare tool.
- **Cura** has inspect + verify + prepare. Failure paths: dangerous commands,
  temp above policy, missing heater shutdown, missing stepper disable, missing
  metadata. `cura_gcode_prepare` adds shutdown/end sequence and returns a new
  artifact — carry the new id forward. Dangerous commands mean re-slice.
- Always show the user the summary and get explicit confirmation before
  transfer. This is the last cheap abort.

### Branch — ready-made G-code

Skip the mesh stages. Import with `kind: "gcode"`, run the Stage 5 review,
then check compatibility: policy temperature caps and the mapped material's
real limits, move bounds against the printer profile's build volume, footer
heater-off / stepper-disable, no dangerous commands, and any macro or firmware
requirement from read-only `moonraker_config` / `moonraker_list_macros`.
Report PASS/FAIL with the tool evidence and stop. No queue, transfer or print
until the user asks in a separate turn; never hand-edit the G-code, and never
invent a "re-slice" fix when no mesh exists.

### Stage 6 — Transfer

- `orca_artifact_export` writes under **export roots** and is approval-gated.
  First call returns a pending `apr_…`; the user decides; retry the identical
  call. `cura_artifact_export` is prepare → `cura_confirm_action`. Both name
  the exact destination in the prompt.
- Default Orca export roots are empty: exports are disabled until configured.
  If no shared root exists, the user must copy the file — say so plainly
  rather than improvising network calls.
- The hand-off check is non-optional: `moonraker_files_list` then
  `moonraker_file_metadata`. The filename in the gcodes root is what
  `moonraker_print_start` expects (relative path).

### Stage 7 — Print & babysit

- `moonraker_printer_status` is the curated snapshot;
  `moonraker_printer_objects` is the escape hatch for exact Klipper objects.
  Keep payloads small.
- Calm cadence: status + temperatures every few minutes early on (first
  layer!), then less often. Report concisely — one line per check unless
  something is off.
- First-layer failure is the most common real-world disaster: recommend the
  user watch the first layer, and pause early rather than print spaghetti.
- Pause → inspect → resume is reversible and preferred over cancel. Cancel is
  for "this cannot recover" and requires explicit user confirmation.
- `moonraker_job_queue_add` is the optional alternative to a direct
  `moonraker_print_start`: call `moonraker_job_queue_status` first, append the
  exact gcodes-root filename, and leave a paused queue paused until the user
  explicitly confirms `moonraker_job_queue_start`. Show the queue again after
  the change.

### Cleanup

Offer to remove the per-job workspace after completion, cancel or abort;
delete it only after explicit confirmation. The same rule applies to slicer
artifacts (`*_artifact_delete` is high risk).
