# Setup and environment check

Use this when the user asks to set up 3d-auto-fabrik, check whether the
stack is ready, verify mcp-orca/mcp-cura/mcp-moonraker, or choose default
printer/material/profile settings.

This is a read-only verification flow with an optional, explicitly-confirmed
defaults file. It never touches hardware and never edits server configs.

## Checklist

1. **Local binaries** — run `sh skills/3d-auto-fabrik/scripts/check-setup.sh`
   if available. Otherwise check `which`/`--version` for `mcp-orca`,
   `mcp-cura`, `mcp-moonraker`.
2. **Slicer health** — `mcp-orca doctor` / `orca_doctor`, `orca_engine_info`,
   `orca_policy_info`, `orca_profile_list`. For Cura: `mcp-cura doctor`,
   `cura_server_info`, `cura_engine_info`, `cura_policy_info`,
   `cura_profile_list`. Orca is usable only when `available: true` **and**
   `slice_command_configured: true`.
3. **Printer health** — `mcp-moonraker doctor`, `moonraker_verify_connection`,
   `moonraker_server_info`, `moonraker_policy_info`, `moonraker_cameras`.
   Read `moonraker_config` only for read-only identity facts (secrets redacted).
4. **Report** — table with status/evidence/fix. State whether the stack is ready
   for mesh/profile work, slicing, supervised printing, or blocked.
5. **Defaults (optional)** — if the user wants them, propose a config file from
   MCP-reported facts. Map material/printer labels to **exact** preset IDs;
   never fuzzy-match. Show the full YAML and write only after explicit user
   confirmation.

## Defaults file

Store preferences only, no secrets:

- Global: `~/.config/3d-auto-fabrik/config.yaml`
- Project-local override: `./3d-auto-fabrik.yaml`

Suggested shape (fill only with values reported by MCP tools / confirmed by the
user):

```yaml
# No secrets/tokens/API keys.
preferred_engine: orca            # orca | cura
temp_root: null                   # null = ${TMPDIR:-/tmp}/3d-auto-fabrik
download_max_bytes: 536870912
handoff:
  mode: manual_copy               # export_root | shared_mount | manual_copy
  export_root: null               # absolute path when mode uses an export root
printers:
  <label>:
    moonraker_host: <from moonraker_server_info>
    klipper_config: <from moonraker_server_info.config_file, if present>
    orca_printer: <exact id/name from orca_profile_list>
    cura_definition: <exact id from cura_profile_list>
    cura_variant: <exact id from cura_profile_list>
    build_volume_mm: [x, y, z]    # confirm from resolved profile
materials:
  <label>:
    orca_filament: <exact id/name from orca_profile_list>
    cura_material: <exact id from cura_profile_list>
```

## Do not do during setup

- Do not edit `mcp-orca.toml`, `mcp-cura.toml`, `mcp-moonraker.toml`, or
  `printer.cfg`.
- Do not change policy switches, temp caps, raw-gcode/host-admin flags, or
  import/export roots.
- Do not store secrets, tokens, or API keys in the defaults file.
- Do not heat, move, home, print, queue-start, export, delete, or call
  emergency stop as part of setup.
- Do not guess missing preset IDs or printer dimensions.
