# Session troubleshooting guide — mcp-orca engine, G-code review, transfer, print flow

How to read: **Symptom** → **Check** → **Fix**. Abstracted from a real session run
with this skill — no machine- or config-specific references; every entry applies
to any setup.

## 1. Engine wiring — the server must run with the engine config

| Symptom | Check | Fix |
| --- | --- | --- |
| Slicing fails though `doctor` reports ok ("slicing not wired") | `orca_engine_info`: `available: true` **and** `slice_command_configured: true` (`engine.preset = "orca"` or `engine.slice_command`) | Start the server with the engine config: pass `--config <path>` on the command line or set `MCP_ORCA_CONFIG` in the server entry's `environment`. Read the engine entry and `engine_info.slice_command_configured`, not just the overall `ok` — they can disagree. |
| The server is never in the session | The server entry exists, but the server may not be running | `mcp-orca doctor` / `orca_engine_info`. A config file does not start anything by itself. |

## 2. Custom `slice_command` — its contract

| Symptom | Check | Fix |
| --- | --- | --- |
| Job "succeeds" but no G-code: "slicer reported success but did not write {gcode}" | Job status / workspace after the run | With a custom `engine.slice_command` the server skips its own gcode collection — the command must write `{gcode}` itself. Wrap in `sh -c` and copy after a successful run: `&& cp "{jobdir}"/plate_*.gcode "{gcode}"` |
| Literal `{model}` in errors ("No such file: .../{model}") | Error text | `{model}`/`{models}` expand only when they are the whole argv element. Use a path like `{jobdir}/model_0.stl` inside shell scripts; `{binary}`, `{jobdir}`, `{gcode}`, `{printer}`, `{filament}`, `{process}` expand anywhere in the string. |
| Built-in preset fails: `... [system:2]: "system"` / `Preset type could not be resolved` | The preset has an `inherits` chain — parent presets live in the slicer's preset containers, not as files next to the job | Use a custom `engine.slice_command` with the original preset paths and the slicer's real config directory. Never copy the config directory to a temp location (absolute preset references break). Never flatten presets by hand (`type = printer`/`machine` → unknown-type errors or a crash); real paths + real datadir slice fine. |

Abstracted shape of a working `slice_command`:

```toml
[engine]
runner = "binary"
preset = "orca"
binary = "<slicer binary>"

slice_command = [
  "sh", "-c",
  "<slicer> \"{jobdir}/model_0.stl\" --datadir \"<slicer config dir>\" --load-settings \"{process};{printer}\" --load-filaments \"{filament}\" --arrange 1 --slice 0 --outputdir \"{jobdir}\" --export-settings \"{jobdir}/orca_effective_settings.json\" && cp \"{jobdir}\"/plate_*.gcode \"{gcode}\"",
]
```

## 3. Import — archives and large models

| Symptom | Check | Fix |
| --- | --- | --- |
| Import refused or the model is missing | Archive entries: absolute paths, `..`, backslashes, symlinks, nested archives | Re-extract into a fresh unique job directory and re-import. Large binaries go through the base64 `data` channel — serve the extracted file from a local HTTP server and convert to base64 in Code Mode; never widen `import_roots` for one job. |

## 4. G-code review — what to check before printing

| Symptom | Check | Fix |
| --- | --- | --- |
| End sequence missing or wrong (no `M104 S0` / `M140 S0` / `M84`) | Read header + footer with `orca_artifact_read_text`; the footer may call a macro | Resolve the macro from read-only printer config. Never hand-edit G-code. A wrong or dangerous end sequence → re-slice with a corrected process preset, never a rewrite. |
| Print looks stalled right after `print_start` (file position stuck, heater targets 0) | Diagnosing too early | Normal during homing and bed heat-up (`M190`); `M109` follows once the bed reaches its target. Wait before treating it as failure. |
| Dangerous commands present (`M112`, `M502`, `M500`, mid-file `G28`, unexpected raw commands) | `orca_gcode_inspect` gives stats; read header + footer | Orca has no dangerous-command scan — find and report them; re-slice, never hand-edit. Temperatures must be within policy caps. |

## 5. Transfer — empty export roots

| Symptom | Check | Fix |
| --- | --- | --- |
| `orca_artifact_export` refused; the file never lands in the printer's `gcodes` root | `orca_policy_info` — `export_roots` empty | Do not widen roots. Upload the G-code with `moonraker_file_upload` instead (`filename`, `data_base64`, `root="gcodes"`), encoding the exact artifact bytes with a real base64 tool. Verify with `moonraker_file_verify` (`verified: true`) and `moonraker_files_list` + `moonraker_file_metadata`; estimated time and filament should match the slicer output. |

## 6. Print flow

| Symptom | Check | Fix |
| --- | --- | --- |
| "file not found" at print start | `moonraker_files_list` | The file never landed in the `gcodes` root — redo the transfer. |
| Approval requested at print start | Approval prompt | Relay id/phrase/risk/summary verbatim and wait. Never invent or reuse ids or phrases, never confirm on the user's behalf (even after "print it"). TTL is short — offer to re-prepare if it expires. |
| Printer identity mismatch (preset label vs live host) | `moonraker_server_info` + user config (`~/.config/3d-auto-fabrik/config.yaml`) | A label is not proof the live host is that machine — confirm identity explicitly before any printer action. |
| Queue not starting | `moonraker_job_queue_status` → `queue_state: "paused"` | A paused queue stays paused (`moonraker_job_queue_start` only on explicit confirmation) — check and mention this always. |

## 7. Safety rules seen in the session

- Tool refuses → relay the refusal and its reason. Don't rephrase, enable the flag, or find another tool.
- Destructive action (`orca_artifact_delete`, job-workspace cleanup) → only with explicit user confirmation.
- After upgrading a binary, refresh the tool reference tables in `references/` (`scripts/generate-tool-reference.py`).
- Use only cataloged tool names and arguments; if a tool is unavailable, say so. Never invent a tool, id, confirmation phrase, path or result — see `tool-discipline.md`.

## 8. Getting help

Collect: `--version` of each server binary, `doctor` output, `print-config` output (secret-free by design), and the exact tool call + error.
