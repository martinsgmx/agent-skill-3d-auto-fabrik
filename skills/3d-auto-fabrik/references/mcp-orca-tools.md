# mcp-orca tool catalog

> Generated from `mcp-orca tools --json` by `scripts/generate-tool-reference.py`.
> Regenerate after any server upgrade. Risk and gate come from the server's
> own policy engine — do not hand-edit this table.

Risk tiers: `read` (no mutation) → `low` → `medium` → `high` → `critical`.
Gates: `policy` (local safety policy), `local` (local info only),
`confirm` (explicit confirmation), `emergency` (emergency only).

Pipeline order: import → mesh inspect/transform/merge → profile resolve → slice → G-code inspect → export/delete. Nothing here contacts the printer. Export and delete require an approval request plus `orca_approval_decide`, then a retry of the identical call.

| Tool | Risk | Gate | Arguments | Description |
| --- | --- | --- | --- | --- |
| `orca_artifact_get` | read | policy | `artifact_id` | Return metadata for one artifact id. |
| `orca_artifact_list` | read | policy | `kind, query, limit` | List stored artifacts, newest first, optionally filtered by kind and a case-insensitive substring query. |
| `orca_artifact_read_text` | read | policy | `artifact_id, start_line, max_lines, max_bytes` | Read a UTF-8 text artifact (e.g. gcode/profile) with line/byte limits. |
| `orca_config_defaults` | read | policy | `—` | Return the first-time printer/filament/process defaults saved in the workspace, including their resolved essentials snapshot and whether setup is complete. |
| `orca_config_profiles` | read | policy | `kind, filter, limit, config_dir, include_bundled, max_presets` | List locally discovered OrcaSlicer printer/filament/process presets from user JSON and system *.opc caches, with optional kind filter and substring filter. |
| `orca_config_resolve` | read | policy | `kind, name, printer, filament, process, overrides, include_settings, config_dir, include_bundled, max_presets` | Resolve one local preset (kind + name) or a printer/filament/process selection, following inherits/includes, and extract the settings needed for a correct print. Uses the local OrcaSlicer config; nothing is invented and merged settings can be returned in full. |
| `orca_config_scan` | read | policy | `config_dir, include_bundled, max_presets` | Scan the local OrcaSlicer configuration directory (user JSON presets plus system *.opc preset caches) with bounded, read-only discovery. Reports discovered roles/counts, the currently active OrcaSlicer selection, and whether first-time defaults are already saved. |
| `orca_doctor` | read | policy | `—` | Run configuration and environment diagnostics. |
| `orca_engine_info` | read | policy | `—` | Return engine runner probe/configuration and availability. |
| `orca_gcode_inspect` | read | policy | `artifact_id` | Inspect a G-code artifact and report computed metrics (heuristic, from commands/markers) and slicer summary metrics (from G-code comments when present). Prefer slicer_summary for user-facing layer/time/filament reporting when available. Reports discrepancies as warnings. Does not execute G-code. |
| `orca_mesh_inspect` | read | policy | `artifact_id` | Inspect a mesh artifact and report bounds, dimensions, triangle/vertex counts, and format. Supports STL (ASCII and binary) and Wavefront OBJ (ASCII, polygons fan-triangulated). |
| `orca_pending_approvals` | read | policy | `—` | List pending, unexpired approval requests for gated actions. |
| `orca_policy_info` | read | policy | `—` | Return effective policy and approval settings. |
| `orca_profile_get` | read | policy | `profile_id` | Get one discovered profile entry by id, path, or name. Returns indexed metadata; native preset parsing is left to the target engine adapter. |
| `orca_profile_list` | read | policy | `kind, query, limit` | List discovered OrcaSlicer presets/profiles from bounded sources (explicit paths + OS-detected common defaults, if enabled) and workspace custom profiles. No whole-system scan. |
| `orca_profile_refresh` | read | policy | `—` | Rescan bounded profile discovery sources and workspace custom profiles. |
| `orca_profile_resolve` | read | policy | `printer, filament, process, profiles, overrides, project` | Resolve effective settings from selected printer/filament/process presets and overrides. Requires essentials (printer+filament+process) unless a supported project is given. Workspace custom profile artifacts (art_*) contribute settings; native presets are resolved by reference; overrides merge last. |
| `orca_server_info` | read | policy | `—` | Return server and configuration summary. |
| `orca_slice_list` | read | policy | `limit` | List known slice jobs, newest first. |
| `orca_slice_status` | read | policy | `job_id` | Get status/result metadata for a slice job. |
| `orca_slice_wait` | read | policy | `job_id, timeout_secs` | Wait for a slice job to complete or time out. |
| `orca_artifact_import` | low | policy | `path, data, name, kind, format, metadata` | Import a file (from an allowed import root) or base64 data into the managed workspace. Returns a content-addressed artifact (same bytes => same id). |
| `orca_artifact_update_metadata` | low | policy | `artifact_id, name, kind, metadata_patch` | Update non-content metadata on a workspace artifact (name, kind, metadata patch). Artifact bytes and content-addressed id are unchanged. Use this to repair misclassified kind or attach metadata; it does not rewrite file contents. |
| `orca_mesh_merge` | low | policy | `artifact_ids, name` | Combine multiple STL/OBJ mesh artifacts into one derived binary STL artifact. Triangles are concatenated in the given order without automatic placement offsets. |
| `orca_mesh_transform` | low | policy | `artifact_id, translate, rotate_deg, scale, mirror, name` | Create a derived mesh artifact by applying translate/rotate/scale (uniform or per-axis) and/or mirror to an STL or OBJ source. Transform order: scale/mirror -> rotate -> translate. Output is always a binary STL artifact. |
| `orca_profile_create` | low | policy | `name, kind, base_profile, settings, metadata` | Create a workspace-managed custom profile/override artifact. Stored in workspace; no mutation of user/system Orca installs. |
| `orca_profile_update` | low | policy | `artifact_id, name, kind, base_profile, settings, metadata` | Update a workspace-managed custom profile artifact by creating a new version (content-addressed). External on-disk profiles are never edited in place. |
| `orca_approval_decide` | medium | policy | `approval_id, approve, note` | Approve or deny a pending approval request. After approval, retry the identical gated call within the approval TTL; the approval is consumed once. |
| `orca_config_setup` | medium | policy | `printer, filament, process, overrides, detect, save, reset, config_dir, include_bundled, max_presets` | First-time setup: detect or accept a printer/filament/process selection from the local OrcaSlicer configuration, resolve it, extract printing essentials, and save it in the workspace so orca_slice can reuse it as default essentials. Explicit arguments win over the detected OrcaSlicer selection. |
| `orca_slice` | medium | policy | `model_artifact_ids, printer, filament, process, project, profiles, overrides, name, wait, wait_timeout_secs` | Start an OrcaSlicer slice job for one or more mesh artifacts using printer/filament/process essentials and overrides. When a role is omitted, the defaults recorded by orca_config_setup are used; explicit arguments always win. Workspace custom profile artifacts contribute merged settings (staged as settings.json); overrides take precedence. Returns a job id immediately unless wait=true. Execution requires engine.preset="orca" or engine.slice_command; otherwise jobs fail with a clear configuration error. |
| `orca_slice_cancel` | medium | policy | `job_id` | Request cancellation of a queued/running slice job. |
| `orca_artifact_delete` | high | policy | `artifact_id` | Remove an artifact from the workspace. May require approval per policy. |
| `orca_artifact_export` | high | policy | `artifact_id, path, overwrite` | Copy an artifact to a destination path under configured workspace.export_roots. May require approval per policy. |
