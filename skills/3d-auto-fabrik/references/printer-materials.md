# Printer, material and profile configuration

Expanded companion to SKILL.md's "Printer, material and profile
configuration". Load this before choosing a printer or a material, and again
whenever a preset cannot be resolved. The live MCP configuration is the
source of truth; the user config is a set of labels and preferences on top.

## User config (preferences only)

Two files, no secrets:

1. `~/.config/3d-auto-fabrik/config.yaml` — global.
2. `./3d-auto-fabrik.yaml` — optional project-local override.

Store labels, exact preset ids and a few paths. Never put API keys, tokens or
passwords in either file: those belong in the MCP servers' environment. The
agent may write these files **only** during explicit onboarding; it never
edits a slicer TOML, `printer.cfg`, or a server's import/export roots.

```yaml
# Illustrative shape — replace every value with one the MCP actually reported.
drop_dir: model_downloaded/files
temp_root: null            # null = ${TMPDIR:-/tmp}/3d-auto-fabrik
download_max_bytes: 536870912
printers:
  voron-m700:              # label chosen by the user
    moonraker_host: klipper-tc-m700   # from moonraker_server_info
    klipper_config: /home/klipper/printer_data/config/printer.cfg
    orca_printer: "<exact id or name from orca_profile_list>"
    cura_definition: "<exact id from cura_profile_list>"
    cura_variant: "<exact id from cura_profile_list>"
    build_volume_mm: [300, 300, 350]  # confirm from the resolved profile
materials:
  petg:
    orca_filament: "<exact id from orca_profile_list>"
    cura_material: "<exact id from cura_profile_list>"
```

A config with no printers or no materials is not an error to work around:
stop and ask the user.

## Live facts to read at every preflight

| Tool | What it gives you |
| --- | --- |
| `orca_server_info` / `cura_server_info` | version, workspace paths, engine and profile-source summary, policy/approval mode |
| `orca_doctor` / `cura_doctor` | per-check health; read the **engine** entry, not just overall `ok` |
| `orca_engine_info` / `cura_engine_info` | engine `available`, resolved path/version, `slice_command_configured` |
| `orca_profile_list` / `cura_profile_list` | the presets the server can actually index, with ids |
| `orca_profile_get` / `cura_profile_get` | details for one indexed id/path/name |
| `moonraker_config` | effective Moonraker config, secrets redacted; read-only |
| `moonraker_server_info` | Klipper host/version/state, `config_file`, registered directories |
| `moonraker_policy_info` | temperature caps, approval mode, mutation switches |
| `moonraker_printer_objects` / `moonraker_list_macros` | loaded heaters, sensors and macros — read with explicit object names |

These tools are read-only. Use their returned values verbatim; do not infer a
printer's build volume, nozzle or temperatures from a directory name.

## Discovery order

1. **Ask the active MCP.** `orca_profile_list` (or `cura_profile_list`) is the
   authority on which presets are usable. Match the user's label to an exact
   id from that list.
2. **If essentials are missing**, ask the user for a directory of preset
   files. Read those files read-only and show what you found. `orca_profile_refresh`
   / `cura_profile_refresh` only helps for directories already inside the
   server's bounded search sources — do not edit `search_paths` to add one.
3. **Bridge carefully.** If a native preset is outside the indexed sources,
   offer to create a workspace-managed custom profile with
   `orca_profile_create` (`base_profile` + `settings`) or to pass `overrides`
   / `profiles` to the slice call where that tool accepts them. Never claim a
   preset resolved unless `orca_profile_resolve` (or `cura_profile_verify`)
   actually says so.
4. **Never force a check.** No config edits, no enabling an engine flag, no
   widening of import/export roots, no `printer.cfg` changes. Quote the
   refusal and stop.
5. **Onboarding, only on request.** If the user asks to "set up this printer"
   or "onboard my slicer", read the live facts above, propose labels → ids,
   ask the user to confirm, and write **only** the user config file. There is
   no automatic background setup.

## Printer identity

Identify a printer by what Moonraker reports — `moonraker_server_info` gives
the Klipper hostname and config path — and map that to the label in the user
config. Several named printers may be configured; the user picks one per job.
When the configured label and the live host disagree, stop and ask rather
than sending a job to the wrong machine.

## Material mapping

A user-facing name is a label, not a preset. Every label (PLA, ABS, PLA silk,
PETG, …) must be mapped by the user to a concrete filament/material preset
from the active MCP. If a label is unmapped, ask — never fuzzy-match the
closest-sounding entry.

These numbers are **documentation examples only**, not defaults and not
authoritative; the selected preset and `moonraker_policy_info` caps always
win:

| Example label | Illustrative nozzle / bed °C |
| --- | --- |
| PLA | 200–220 / 55–65 |
| PLA silk | 200–225 / 55–65 |
| ABS | 230–250 / 90–110 |
| PETG | 230–250 / 70–85 |

Use the mapped material's real limits when reviewing a ready-made G-code file
(the G-code-only branch in SKILL.md), and re-check them against the server's
temperature caps. A profile that exceeds those caps is reported, never
silently clamped.
