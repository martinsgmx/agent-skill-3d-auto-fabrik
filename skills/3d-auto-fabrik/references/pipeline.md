# The mesh → print pipeline in detail

Expanded companion to SKILL.md. Load this when you are actually running a
job. Tool names are exact; risk tiers and gates are the server's own.

## Example dialogue (abbreviated)

> **User:** Slice ~/Downloads/bracket.stl on the Voron, PETG, 0.2 quality.
> **Agent:** Importing and inspecting first… (`cura_artifact_import` →
> `artifact_id=art_01J…`; `cura_mesh_inspect`: 84 bounds-clean triangles,
> watertight, 12.4 cm³, 41 × 38 × 25 mm)
> …
> **Agent:** Resolve shows PETG at 245 °C hotend / 80 °C bed — under both
> policy caps, verify is clean. Slice complete: 3 h 12 m, 11.4 m of filament.
> `cura_gcode_verify`: OK (heater off, steppers off, no dangerous commands).
> **Shall I send it to the printer?**
> **User:** Yes.
> **Agent:** Exporting to the gcodes share and confirming `moonraker_file_metadata` matches (3 h 09 m — Cura printed 3 h 12 m est; fine). Starting print — you'll get an approval prompt in chat:
> `apr_09XY… "print_start bracket.gcode" — approve with this phrase: FRONT-…`
> **User:** Approved.
> **Agent:** `moonraker_confirm_action` → print started. I'll check in every few minutes; tell me if anything looks off, or say "pause".

## Stage details and pitfalls

### Stage 1 — Import

- mcp-cura imports only from configured **import roots**
  (`~/Downloads`, `~/Documents`, `~/Desktop`, `~/models` by default) or from
  base64 `data`. The roots confine filesystem paths; the `data` parameter is
  the sanctioned channel for client-supplied bytes — it is not a policy
  bypass and needs no config change.
- A path outside the roots is refused. Re-import the same bytes via `data`;
  do not ask the user to widen the roots just for one job, and do not treat
  the refusal as "import is impossible".
- `kind` can hint `mesh` / `gcode` / `profile`; when in doubt pass
  `format: "stl"` (or the right format) — the first import of a byte string
  records its kind and re-importing the same bytes returns the same id.

### Stage 2 — Inspect & repair

- Report: triangle count, bounds, watertightness, volume. If bounds exceed
  the printer's build volume, stop — propose `cura_mesh_transform` scale or
  ask whether to split.
- `cura_mesh_boolean` uses voxelization; `voxel_size` trades detail for
  memory. Compare against the policy's `max_voxel_cells`.
- `cura_mesh_merge` is not a boolean — overlapping shells remain.

### Stage 3 — Profile resolve & verify

- `definition` is the machine definition (e.g. `voron24_0.4`); quality /
  material / variant / intent are profile ids from `cura_profile_list`.
- `cura_profile_resolve` merges all layers and warns about unevaluatable Cura
  expressions. **Warnings are for humans to read**; quote them.
- `cura_profile_verify` returns errors and warnings with setting names.
  Zero errors is the bar for slicing.

### Stage 4 — Slice

- Prefer `wait=true` with `wait_timeout_secs` for typical prints; for very
  large meshes, poll `cura_slice_status`.
- Slice jobs are background work; on timeout, keep polling — the job may
  still finish. `keep_jobs` caps retained job records.

### Stage 5 — G-code review

- `cura_gcode_inspect` lists **maximum temperatures** anywhere in the file.
  Anything near or above the cap deserves a call-out even if verify passed.
- `cura_gcode_verify` failure paths: dangerous commands, temp above policy,
  missing heater shutdown, missing stepper disable, missing metadata. Fix via
  `cura_gcode_prepare` (adds shutdown; `ensure_final_newline`; optionally a
  full end sequence) or re-slice. Carry the new artifact id forward.

### Stage 6 — Transfer

- `cura_artifact_export` writes under **export roots** and is high risk:
  the prepare prompt names the exact destination. It cannot write anywhere
  else — that is the sandbox working as designed.
- The hand-off check is non-optional: `moonraker_files_list` then
  `moonraker_file_metadata`. The filename in the gcodes root is what
  `moonraker_print_start` expects (relative path).
- There is no MCP upload tool. If no shared root is available, the user must
  copy the file — say so plainly rather than improvising network calls.

### Stage 7 — Print & babysit

- `moonraker_printer_status` is the curated snapshot;
  `moonraker_printer_objects` is the escape hatch for exact Klipper objects
  (`objects={"heater_bed": ["temperature"]}` style). Keep payloads small.
- Calm cadence: status + temperatures every few minutes early on (first
  layer!), then less often. Report concisely — one line per check unless
  something is off.
- First-layer failure is the most common real-world disaster: recommend the
  user watch the first layer, and pause early rather than print spaghetti.
- Pause → inspect → resume is reversible and preferred over cancel. Cancel is
  for "this cannot recover" and requires explicit user confirmation.
