---
description: Check 3d-auto-fabrik environment, verify MCP servers, and configure safe defaults
---

Set up and verify the local 3d-auto-fabrik environment. This is a read-only health check plus an optional, explicitly-confirmed defaults file. It must never touch hardware, never self-approve, and never edit server policy/config files.

## Rules

- **Read-only checks only.** You may run local doctor/version commands, MCP read/info tools, `moonraker_verify_connection`, status/config/policy/profile list tools, and camera listing. Do not heat, move, home, start, pause, resume, cancel, queue-start, export, delete, or send raw G-code.
- **No server config edits.** Do not edit `mcp-orca.toml`, `mcp-cura.toml`, `mcp-moonraker.toml`, Klipper config, or any server policy switch. If something is missing, report the exact user-side fix.
- **No secrets in files.** Never write `MOONRAKER_API_KEY`, HTTP tokens, passwords, or private credentials into any file. Secrets stay in environment variables / server config managed by the user.
- **Write defaults only after explicit confirmation.** Before creating or changing `~/.config/3d-auto-fabrik/config.yaml` or `./3d-auto-fabrik.yaml`, show the complete proposed file and ask for a clear "yes, write it".
- **Be honest.** If a server is missing, unreachable, or an engine is unconfigured, say so plainly. Do not guess printer names, preset IDs, materials, or build volumes.

## 1) Local binaries / CLI check

Run from the skill repo (or locate `check-setup.sh`):

```sh
sh skills/3d-auto-fabrik/scripts/check-setup.sh
```

If the script is not available, check manually: `which mcp-orca mcp-cura mcp-moonraker` and `mcp-orca --version` / `mcp-cura --version` / `mcp-moonraker --version`.

## 2) MCP/server health

For each installed server, collect read-only diagnostics:

- **mcp-orca**: `mcp-orca doctor --config "$MCP_ORCA_CONFIG"` when configured, else `mcp-orca doctor`; then MCP `orca_server_info`, `orca_engine_info`, `orca_policy_info`, `orca_profile_list` (small limit/sample if large).
- **mcp-cura**: `mcp-cura doctor`; MCP `cura_server_info`, `cura_engine_info`, `cura_policy_info`, `cura_profile_list`.
- **mcp-moonraker**: `mcp-moonraker doctor`; MCP `moonraker_verify_connection`, `moonraker_server_info`, `moonraker_policy_info`, `moonraker_cameras`, `moonraker_config` only if needed for printer identity facts (read-only, secrets redacted).

Determine engine readiness:
- Orca usable only when `available: true` **and** `slice_command_configured: true`.
- Cura usable when its doctor/engine info reports a reachable engine.
- Default engine = Orca if usable, else Cura if usable, else blocked.

## 3) Readiness report

Produce a compact table with: component, status (`ok/warn/missing/blocked`), evidence, and user action. Include at least: mcp-orca binary, Orca engine, Orca profiles, mcp-cura binary, Cura engine, mcp-moonraker binary, Moonraker reachable, Klipper state, approval modes, temp caps, import/export roots or handoff path.

End with one line: `Ready for mesh/profile work`, `Ready for slicing`, `Ready for supervised printing`, or `Blocked` — and why.

## 4) Optional defaults (ask, then write)

If the user wants defaults configured, ask them to confirm:

- Preferred engine (`orca` or `cura`, defaulting to the ready one).
- Printer label and which Moonraker host/Klipper identity it maps to.
- Default nozzle / process / quality preset.
- Material labels mapped to **exact** preset IDs from `orca_profile_list` / `cura_profile_list` (never fuzzy-match). For each material, capture the preset id/name as reported.
- G-code handoff preference: export root path, shared gcodes mount, or manual copy.
- Where to save: `~/.config/3d-auto-fabrik/config.yaml` (global) or `./3d-auto-fabrik.yaml` (project-local).

Before writing, show the proposed YAML in full. Use this shape only with values confirmed by the user and/or reported by MCP tools:

```yaml
# 3d-auto-fabrik user defaults — no secrets/tokens/API keys
preferred_engine: orca
temp_root: null
download_max_bytes: 536870912
handoff:
  mode: manual_copy   # export_root | shared_mount | manual_copy
  export_root: null
printers:
  <label>:
    moonraker_host: <from moonraker_server_info>
    klipper_config: <from moonraker_server_info.config_file, if present>
    orca_printer: <exact id/name from orca_profile_list>
    cura_definition: <exact id from cura_profile_list>
    cura_variant: <exact id from cura_profile_list>
    build_volume_mm: [x, y, z]  # confirm from resolved profile
materials:
  <label>:
    orca_filament: <exact id/name from orca_profile_list>
    cura_material: <exact id from cura_profile_list>
```

Only write after the user explicitly confirms. After writing, print the file path and a short "how to change it" note.

## 5) Final summary

Report what was checked, what is ready, what is blocked, what defaults were written (if any), and the safest next command/action (e.g. "ask me to slice a model" or "configure Orca engine preset"). Do not start a print.
