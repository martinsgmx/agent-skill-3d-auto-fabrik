# mcp-cura tool catalog

> Generated from `mcp-cura tools --json` by `scripts/generate-tool-reference.py`.
> Regenerate after any server upgrade. Risk and gate come from the server's
> own policy engine — do not hand-edit this table.

Risk tiers: `read` (no mutation) → `low` → `medium` → `high` → `critical`.
Gates: `policy` (local safety policy), `local` (local info only),
`confirm` (explicit confirmation), `emergency` (emergency only).

Pipeline order: import → mesh ops → profile resolve/verify → slice → G-code review → export/delete. Nothing here contacts the printer.

| Tool | Risk | Gate | Arguments | Description |
| --- | --- | --- | --- | --- |
| `cura_artifact_get` | read | policy | `artifact_id` | Return metadata for one artifact id, including kind, format, size, SHA-256, source, and any recorded metadata. |
| `cura_artifact_list` | read | policy | `kind, query, limit` | List stored artifacts, newest first, optionally filtered by kind and a case-insensitive name/id/hash substring. |
| `cura_artifact_read_text` | read | policy | `artifact_id, start_line, max_lines, max_bytes` | Read a UTF-8 text artifact such as G-code or a profile with byte and line limits. Use a line range to page through large files. |
| `cura_engine_info` | read | local | `—` | Probe the configured CuraEngine binary or Docker image and report availability, version, resolved path, search paths, and settings mode. |
| `cura_gcode_inspect` | read | policy | `artifact_id` | Summarise a G-code artifact: line/command counts, layer count, Z range, estimated time, filament usage, maximum temperatures, and dangerous commands. This is a read-only text analysis. |
| `cura_gcode_verify` | read | policy | `artifact_id` | Check a G-code artifact for dangerous commands, temperatures above the local safety policy, missing heater shutdown, missing stepper disable, and missing metadata. |
| `cura_mesh_inspect` | read | policy | `artifact_id` | Report triangle and vertex counts, bounds in millimetres, surface area, volume, watertightness, boundary/non-manifold edges, and degenerate triangles for a mesh artifact. |
| `cura_pending_approvals` | read | local | `all` | List prepared high-risk actions waiting for confirmation. Use cura_confirm_action with an approval id to execute one. |
| `cura_policy_info` | read | local | `—` | Report the active local safety policy, limits, and approval mode. Use this before attempting a write, process, export, or delete action. |
| `cura_profile_get` | read | policy | `profile_id, include_settings, settings_limit` | Load one profile by id, name, or path. Definitions return their merged setting catalog and inheritance lineage; instances and materials return their parsed values and metadata. |
| `cura_profile_list` | read | policy | `kind, query, limit` | List discovered definitions, quality, material, variant, intent, user, and custom profiles. Filter by kind and a case-insensitive name/path substring. Use the returned id with the other profile tools. |
| `cura_profile_refresh` | read | policy | `—` | Rescan configured profile directories. Returns counts by kind and any files that were skipped. Call after writing a custom profile outside the workspace. |
| `cura_profile_resolve` | read | policy | `definition, quality, quality_changes, material, variant, intent, profiles, overrides, extruders, include_settings` | Resolve a definition plus quality, material, variant, intent, custom, and caller layers into one settings map. Includes warnings for Cura expressions that cannot be evaluated and hard temperature violations. |
| `cura_profile_verify` | read | policy | `definition, quality, quality_changes, material, variant, intent, profiles, overrides, extruders` | Resolve a profile and check machine dimensions, extruder count, nozzle size, temperatures, layer height, line width, and speed. Returns errors and warnings with the offending setting names. |
| `cura_server_info` | read | local | `—` | Report mcp-cura version, workspace paths, transport, policy summary, approval mode, and engine configuration. Secrets are omitted. |
| `cura_slice_list` | read | policy | `limit` | List recent slice jobs, newest first, with state and artifact ids. |
| `cura_slice_status` | read | policy | `job_id` | Return one slice job record, including state, timings, engine log tail, error, and (when complete) the G-code artifact and statistics. |
| `cura_slice_wait` | read | policy | `job_id, timeout_secs` | Wait until a job reaches a terminal state or the timeout elapses, then return the record. Prefer polling cura_slice_status for long jobs. |
| `cura_artifact_import` | low | policy | `path, data, name, kind, format, metadata` | Copy a mesh, G-code file, or profile into the managed workspace and return a stable content-addressed artifact id. Supply either an absolute path under the configured import roots or base64 data. Importing the same bytes twice returns the same id. |
| `cura_gcode_prepare` | low | policy | `artifact_id, add_end_temperature, add_end_sequence, ensure_final_newline, name` | Create a new G-code artifact with a safe heater shutdown and optionally a full end sequence (fan off, lift, home X/Y, steppers off). Refuses files that contain dangerous commands. The original artifact is unchanged. |
| `cura_profile_create` | low | policy | `definition, name, values, setting_version` | Write a custom quality-changes `.inst.cfg` into the workspace and import it as a profile artifact. The definition must already be discoverable. Values are written verbatim under [values]. |
| `cura_slice_cancel` | low | policy | `job_id` | Cancel a queued or running slice job. A running engine process is killed and the job is marked cancelled. Completed jobs cannot be cancelled. |
| `cura_mesh_boolean` | medium | policy | `left_artifact_id, right_artifact_id, operation, voxel_size, name` | Voxel-based union, subtract, or intersect of two mesh artifacts. Voxel resolution trades detail for memory; the policy caps estimated cells. |
| `cura_mesh_decimate` | medium | policy | `artifact_id, target_triangles, name` | Reduce triangle count towards a target while keeping the overall shape. The result is a new mesh artifact; the original is unchanged. |
| `cura_mesh_merge` | medium | policy | `artifact_ids, name` | Concatenate two or more mesh artifacts into one triangle soup. This is not a boolean union; overlapping shells remain. Use cura_mesh_boolean for a true union. |
| `cura_mesh_offset` | medium | policy | `artifact_id, distance, voxel_size, name` | Expand (positive) or shrink (negative) a closed mesh by a distance in millimetres using a signed-distance volume. |
| `cura_mesh_remesh` | medium | policy | `artifact_id, voxel_size, name` | Rebuild a mesh surface at a new voxel resolution. Useful to clean up self-intersections before slicing, at the cost of detail. |
| `cura_mesh_transform` | medium | policy | `artifact_id, name, translate, scale, rotate, mirror, center_on_bed` | Translate, scale, rotate (XYZ Euler degrees), mirror, and/or center a mesh on the bed, producing a new mesh artifact. Transform order is scale, rotate, translate, mirror, then centering. |
| `cura_slice` | medium | policy | `model_artifact_ids, definition, quality, quality_changes, material, variant, intent, profiles, overrides, extruders, model_overrides, name, threads, wait, wait_timeout_secs` | Resolve a Cura profile and start a background CuraEngine slice for one or more mesh artifacts. Returns a job id immediately unless wait=true. The G-code is imported as an artifact when the job completes. |
| `cura_artifact_delete` | high | policy | `artifact_id` | Remove one artifact and its blob from the workspace. Approval-gated and irreversible; job records that reference the artifact are kept. |
| `cura_artifact_export` | high | policy | `artifact_id, path, overwrite` | Copy an artifact to an absolute path under the configured export roots. This is approval-gated because it can overwrite user-visible files. The action summary names the exact destination. |
| `cura_confirm_action` | high | confirm | `approval_id, confirmation_phrase, acknowledge` | Execute a previously prepared high-risk action. The stored tool and arguments are used; supplying different arguments here does nothing. Requires acknowledge=true and, depending on approval mode, a single-use confirmation phrase and/or human out-of-band approval. |
