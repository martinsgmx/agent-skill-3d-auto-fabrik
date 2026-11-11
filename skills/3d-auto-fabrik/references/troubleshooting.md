# Troubleshooting

Both servers share the same CLI shape: `serve` (default stdio), `doctor`,
`pending`, `approve`/`deny`, `tools`, `print-config`, `init`. Cura and
Moonraker each check their own domain.

## mcp-cura

| Symptom | Check | Fix (user-side unless noted) |
| --- | --- | --- |
| Server not found | `which mcp-cura` | build from the sibling repo: `cargo install --path <path>/mcp-cura` |
| `doctor` fails on engine | `mcp-cura doctor` → engine section | Install CuraEngine; set `[engine] runner = "docker"` + pinned image; confirm with `cura_engine_info` |
| `doctor` warns on profiles | profile count 0 | Set `[profiles] dirs` or `auto_discover = true`; open Cura once to generate profiles; `cura_profile_refresh` |
| Import rejected | path outside roots | Ask user to move the file, or pass `data` base64 |
| Slice fails instantly | `cura_slice_status` log tail | Usually bad profile: `cura_profile_verify` errors quote the offending settings |
| Slice hangs | `cura_slice_status` | `cura_slice_cancel`; check `max_slice_secs` / `max_triangles` policy |
| G-code verify fails | `cura_gcode_verify` output | `cura_gcode_prepare` for missing shutdown; re-slice for dangerous commands — never hand-edit the artifact |
| "approval expired" | `cura_pending_approvals` | Re-prepare; TTL is short by design |

## mcp-moonraker

| Symptom | Check | Fix |
| --- | --- | --- |
| Server not found | `which mcp-moonraker` | build from the sibling repo: `cargo install --path <path>/mcp-moonraker` |
| Unreachable printer | `mcp-moonraker doctor`, then `moonraker_verify_connection` | Moonraker not running (`systemctl status moonraker`), wrong `[moonraker] url`, firewall; **do not** enable host admin to "fix" connectivity |
| "moonraker is in shutdown state" | `moonraker_server_info` / `moonraker_gcode_history` | Klipper hit an error (thermal runaway, MCU shutdown). Physical inspection first; restarts only when the user asks |
| Temperatures stuck / heater refuses | `moonraker_policy_info` vs target | Server temp caps (default 300/120 °C) — deliberate; only the owner raises them |
| Raw G-code rejected | policy shows `allow_raw_gcode = false` | Leave it off; use structured tools (`home_axes`, `move_axis`, `run_macro`) |
| Print start says "file not found" | `moonraker_files_list` | The file never landed in the gcodes root — redo Stage 6 transfer |
| Camera snapshot empty | `moonraker_cameras` | Camera not enabled in Moonraker, or `allow_private_hosts`/`allowed_hosts` blocking; report, don't bypass |
| Tool call refused by client | client permissions | The client (opencode permissions, Claude permissions…) filters MCP tools — see `docs/platforms.md` |

## Both servers

- **Version skew**: after upgrading either binary, re-run
  `scripts/generate-tool-reference.py` to refresh the catalogs in
  `references/`. The servers print `--version`.
- **Config precedence**: built-in defaults < TOML file < environment
  variables < CLI flags. Check `mcp-cura print-config` /
  `mcp-moonraker print-config` to see the *effective* configuration —
  this is the fastest way to spot an env var shadowing the file.
- **Secrets**: `print-config` is secret-free by design. API keys live in
  environment variables (`MOONRAKER_API_KEY`, `MCP_CURA_HTTP_TOKEN`, …),
  never in the TOML.
- **Approval weirdness after restart**: list pending approvals; TTL-exired
  ones are dead — re-prepare.

## Getting help

Collect: `--version` of the binary, `doctor` output, `print-config` output
(already secret-free), and the exact tool call + error. File an issue using
`.github/ISSUE_TEMPLATE/bug_report.yml`.
