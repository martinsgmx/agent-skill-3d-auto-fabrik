# Troubleshooting

All three servers share the same CLI shape: `serve` (default stdio), `doctor`,
`tools`, `print-config`, `init`, and approval commands. Each checks its own
domain. If mcp-orca is unavailable, the skill falls back to mcp-cura.

## mcp-orca

| Symptom | Check | Fix (user-side unless noted) |
| --- | --- | --- |
| Server not found | `which mcp-orca` | build from the sibling repo: `cargo install --path <path>/mcp-orca` |
| `doctor` says engine unavailable | `mcp-orca doctor`, `orca_engine_info` | Install `orca-slicer`; set `[engine] preset = "orca"` (and `binary`) or a `slice_command`; for Docker set `runner = "docker"` + `docker_image` |
| No profiles found | `orca_profile_list`, `orca_profile_get`, `mcp-orca doctor` | The list is a bounded index, not proof of absence: try an exact path with `orca_profile_resolve` before concluding unavailable. User may set `[profiles] search_paths` or open Orca once, then `orca_profile_refresh` |
| "missing printer/filament/process" | `orca_profile_resolve` error | Orca requires all three native presets; no invented defaults. Pick them from `orca_profile_list` |
| "did not resolve to a .json file" | resolve/selection warnings | Pass a preset path, add its directory to `search_paths`, or set `base_profile` on the workspace profile artifact |
| Import rejected | `orca_policy_info`, `print-config` | `workspace.import_roots` defaults to empty. Import via base64 `data`, or ask the owner to add a root |
| Imported mesh shows `kind:other` / "not a mesh" | `orca_artifact_get`, then `orca_mesh_inspect` only if the kind is `mesh` | (agent-side) Report metadata verbatim; re-import original bytes with explicit `kind`/`format`. Same content-addressed id means an upstream classification issue — stop/ask. A harmless header change is a last-resort diagnostic, never a geometry fix |
| Export refused | `orca_policy_info`, `print-config` | `workspace.export_roots` defaults to empty. Add a root, or have the user copy the file |
| Slice fails instantly | `orca_slice_status` → `error` | Usually no engine invocation configured, or a preset that is not native `.json`; quote the error |
| Slice hangs | `orca_slice_status` | `orca_slice_cancel`; check `engine.timeout_secs` and `max_concurrent_jobs` |
| G-code review feels thin | `orca_gcode_inspect` output | Orca has no verify tool. Read header/footer with `orca_artifact_read_text`; re-slice if the end sequence is wrong |
| Inspect numbers disagree with the G-code header | `orca_gcode_inspect`, `orca_artifact_read_text`, `moonraker_file_metadata` after transfer | (agent-side) Cross-check inspect vs header/config summary vs Moonraker metadata and report the discrepancy. Do not block on a numbers-only mismatch; temperatures, dangerous commands, heater-off and `M84` still gate. Never hand-edit |
| "approval expired" / pending | `orca_pending_approvals` | Re-run the gated call; TTL is short by design |

## mcp-cura

| Symptom | Check | Fix |
| --- | --- | --- |
| Server not found | `which mcp-cura` | `cargo install --path <path>/mcp-cura` |
| `doctor` fails on engine | `mcp-cura doctor` → engine section | Install CuraEngine; set `[engine] runner = "docker"` + pinned image; confirm with `cura_engine_info` |
| `doctor` warns on profiles | profile count 0 | Set `[profiles] dirs` or `auto_discover = true`; open Cura once; `cura_profile_refresh` |
| Import rejected | path outside roots | Move the file, or pass `data` base64 |
| Slice fails instantly | `cura_slice_status` log tail | Usually a bad profile: `cura_profile_verify` errors quote the offending settings |
| Slice hangs | `cura_slice_status` | `cura_slice_cancel`; check `max_slice_secs` / `max_triangles` policy |
| G-code verify fails | `cura_gcode_verify` output | `cura_gcode_prepare` for missing shutdown; re-slice for dangerous commands — never hand-edit |
| "approval expired" | `cura_pending_approvals` | Re-prepare; TTL is short by design |

## mcp-moonraker

| Symptom | Check | Fix |
| --- | --- | --- |
| Server not found | `which mcp-moonraker` | `cargo install --path <path>/mcp-moonraker` |
| Unreachable printer | `mcp-moonraker doctor`, then `moonraker_verify_connection` | Moonraker not running (`systemctl status moonraker`), wrong `[moonraker] url`, firewall; **do not** enable host admin to "fix" connectivity |
| "moonraker is in shutdown state" | `moonraker_server_info` / `moonraker_gcode_history` | Klipper hit an error (thermal runaway, MCU shutdown). Physical inspection first; restarts only when the user asks |
| Temperatures stuck / heater refuses | `moonraker_policy_info` vs target | Server temp caps (default 300/120 °C) — deliberate; only the owner raises them |
| Raw G-code rejected | policy shows `allow_raw_gcode = false` | Leave it off; use structured tools (`home_axes`, `move_axis`, `run_macro`) |
| Print start says "file not found" | `moonraker_files_list` | The file never landed in the gcodes root — redo Stage 6 transfer |
| Camera snapshot empty | `moonraker_cameras` | Camera not enabled in Moonraker, or `allow_private_hosts`/`allowed_hosts` blocking; report, don't bypass |
| Tool call refused by client | client permissions | The client filters MCP tools — see `docs/platforms.md` |

## All servers

- **Version skew**: after upgrading any binary, re-run
  `scripts/generate-tool-reference.py` to refresh the catalogs in
  `references/`. The servers print `--version`.
- **Config precedence**: built-in defaults < TOML file < environment
  variables < CLI flags. Check `mcp-orca print-config` /
  `mcp-cura print-config` / `mcp-moonraker print-config` to see the
  *effective* configuration — this is the fastest way to spot an env var
  shadowing the file.
- **Secrets**: `print-config` is secret-free by design. API keys and tokens
  live in environment variables (`MOONRAKER_API_KEY`,
  `MCP_ORCA_HTTP_TOKEN`, `MCP_CURA_HTTP_TOKEN`, …), never in the TOML.
- **Approval weirdness after restart**: list pending approvals; TTL-expired
  ones are dead — re-prepare.
- **Engine choice**: if `mcp-orca doctor` fails but `mcp-cura doctor` is
  healthy, use Cura for the whole job. Do not pass artifact ids between them.
- **User names a Cura profile but Cura is unavailable**: say so, search the
  active slicer for the same/closest preset name, show exact ids/paths, and
  require explicit confirmation before using an Orca preset. Never silently
  substitute — see `engine-selection.md`.
- **Large import in Code Mode**: `node:fs` may be unavailable and `file://`
  fetch blocked. Use the scoped, localhost-only staging pattern in
  `job-workspace.md`; kill the helper server and delete staged bytes in the
  same turn, including on failure.
- **No export root / no upload tool**: use the transfer decision table in
  `pipeline.md`. A same-host copy is an explicitly requested, logged exception
  with SHA-256 and Moonraker metadata verification — never a silent widening
  of export roots.

## Getting help

Collect: `--version` of the binary, `doctor` output, `print-config` output
(already secret-free), and the exact tool call + error. File an issue using
`.github/ISSUE_TEMPLATE/bug_report.yml`.
