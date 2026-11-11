# mcp-moonraker tool catalog

> Generated from `mcp-moonraker tools --json` by `scripts/generate-tool-reference.py`.
> Regenerate after any server upgrade. Risk and gate come from the server's
> own policy engine — do not hand-edit this table.

Risk tiers: `read` (no mutation) → `low` → `medium` → `high` → `critical`.
Gates: `policy` (local safety policy), `local` (local info only),
`confirm` (explicit confirmation), `emergency` (emergency only).

Read-only tools first (`printer_status`, `temperatures`, `server_info`), reversible mutations next, double-confirmed destructive tools last. `moonraker_emergency_stop` bypasses gates by design.

| Tool | Risk | Gate | Arguments | Description |
| --- | --- | --- | --- | --- |
| `moonraker_camera_snapshot` | read | policy | `camera, max_bytes` | Capture and return the current frame from a Moonraker webcam as an MCP image. If exactly one camera is enabled, 'camera' may be omitted. With multiple enabled cameras, pass the camera name explicitly. |
| `moonraker_cameras` | read | policy | `—` | List webcams configured in Moonraker, including whether each is enabled and whether a snapshot URL is available. Use this before requesting a snapshot if the camera name is unknown. |
| `moonraker_cancel_approval` | read | local | `approval_id` | Cancel a pending approval so it can never be executed. Safe and immediate; does not affect the printer. |
| `moonraker_config` | read | policy | `section` | Return Moonraker's effective configuration (or one top-level section). Secrets such as API keys, passwords, and tokens are redacted. This is the authoritative read path for configuration; writing configuration is not supported. |
| `moonraker_endstops` | read | policy | `—` | Return the current state of every configured endstop (`open` or `TRIGGERED`). Useful for diagnosing homing failures. |
| `moonraker_file_metadata` | read | policy | `filename` | Return Moonraker's metadata for a G-code file: estimated print time, filament usage, layer height, thumbnails, and slicer information when available. The filename is relative to the 'gcodes' root. |
| `moonraker_files_list` | read | policy | `root, path, limit` | List files and directories under a Moonraker file root (default 'gcodes'). Read-only; paths are relative to the root. |
| `moonraker_gcode_history` | read | policy | `count` | Return recent G-code console messages from Moonraker's in-memory store. Useful for diagnosing command errors and macro output. |
| `moonraker_job_queue_status` | read | policy | `—` | Return the job queue state and all queued jobs. |
| `moonraker_list_macros` | read | policy | `—` | List the `gcode_macro` objects currently loaded in Klipper, with their defined variables when present. Use this before moonraker_run_macro to pick a valid macro name. Read-only. |
| `moonraker_pending_approvals` | read | local | `—` | List prepared destructive actions that are still waiting for confirmation. The agent can use this after a restart or to recover an approval id. |
| `moonraker_policy_info` | read | local | `—` | Return the MCP server's local safety policy: read-only and mutation switches, temperature limits, approval mode, and whether raw G-code and host administration are enabled. Contains no secrets. |
| `moonraker_print_history` | read | policy | `limit, start` | Return completed/failed print jobs from Moonraker's history database, newest first. Includes status, duration, filament used, and metadata. |
| `moonraker_printer_objects` | read | policy | `objects, fields` | List loaded Klipper printer objects or query selected objects. Use the list form to discover objects such as heaters, fans, macros, and sensors; use the query form with explicit object names and optional field lists to avoid returning large payloads. |
| `moonraker_printer_status` | read | policy | `—` | Return a curated snapshot of printer state: print job state and progress, positions, homing state, speeds and factors, fan speed, idle state, and main heater temperatures. Prefer this for broad status questions. |
| `moonraker_server_info` | read | policy | `—` | Return Moonraker's version/components/connection state and Klipper's host information. Use this first to confirm the printer is reachable and whether Klipper is ready, busy, or shut down. |
| `moonraker_system_info` | read | policy | `—` | Return host CPU, memory, distribution, service state, network, and process statistics reported by Moonraker. Useful for diagnosing host resource pressure and service health. |
| `moonraker_temperature_history` | read | policy | `sensors, limit` | Return recent temperature samples from Moonraker's in-memory temperature store. Optionally filter by sensor names and limit the number of samples per sensor (newest kept). |
| `moonraker_temperatures` | read | policy | `—` | Return current and target temperatures for every heater, heated bed, temperature sensor, and temperature-controlled fan. Use this for 'what is the nozzle/bed/chamber temperature?' questions. |
| `moonraker_update_status` | read | policy | `—` | Return Moonraker's update manager status for Klipper, Moonraker, and other configured components, including available versions and dirty states. Read-only. |
| `moonraker_verify_connection` | read | policy | `—` | Probe Moonraker and report whether this MCP server can reach it: connected flag, round-trip latency, Moonraker/Klipper versions, and — on failure — a classified diagnosis with next steps. Always call this first (or before retrying) when another moonraker_* tool fails with a transport error or an unauthorized error. Read-only, never blocks, never mutates. |
| `moonraker_job_queue_add` | low | policy | `filenames` | Append one or more G-code files (relative to the gcodes root) to the job queue. Does not clear the existing queue. |
| `moonraker_set_fan` | low | policy | `fan, percent` | Set a controllable fan speed by percent (0-100). Supported fans are the part-cooling fan ('fan', controlled with M106) and fan_generic objects (controlled with SET_FAN_SPEED). Automatic fans such as heater_fan and temperature_fan are rejected because Klipper manages them. |
| `moonraker_set_flow_factor` | low | policy | `percent` | Set Klipper's extrusion flow factor with M221 (percentage, 50-150). This changes extrusion scaling for subsequent moves and is reversible. |
| `moonraker_set_speed_factor` | low | policy | `percent` | Set Klipper's speed factor with M220 (percentage, 10-200). This changes feedrate scaling for subsequent moves and is reversible. |
| `moonraker_home_axes` | medium | policy | `axes` | Run G28 for the selected axes. Defaults to all axes. Homing moves the toolhead, so ensure the bed is clear. This is a reversible mutation and does not require approval. |
| `moonraker_job_queue_jump` | medium | policy | `job_id` | Move a queued job to the front of the queue. |
| `moonraker_job_queue_pause` | medium | policy | `—` | Pause the job queue so no further jobs load after the current job. |
| `moonraker_job_queue_start` | medium | policy | `—` | Start/resume the job queue so the next queued job can load when Klipper is ready. |
| `moonraker_move_axis` | medium | policy | `axis, distance, speed` | Move X or Y by a relative amount, or move Z upward. The axis must already be homed. Downward Z moves are intentionally rejected. The G-code coordinate state is saved and restored around the move. Does not require approval. |
| `moonraker_print_pause` | medium | policy | `—` | Pause the active print job. Reversible with moonraker_print_resume. |
| `moonraker_print_resume` | medium | policy | `—` | Resume a paused print job. |
| `moonraker_set_heater` | medium | policy | `heater, temperature` | Set the target temperature of a heater or the heated bed. The heater name must be a loaded Klipper object (for example 'extruder' or 'heater_bed'). Targets are capped by the server's configured safety limits. Use temperature 0 to turn a heater off. This is a reversible mutation and does not require approval. |
| `moonraker_turn_off_heaters` | medium | policy | `—` | Turn off every heater and the heated bed immediately. This is a reversible safety-oriented mutation and does not require approval. |
| `moonraker_confirm_action` | high | confirm | `approval_id, confirmation_phrase, acknowledge` | Second step of the double-confirmation flow. Pass the approval id from the prepare response, the confirmation phrase shown to the user (in in-band mode), and acknowledge=true. The server executes the exact tool and arguments that were prepared; it never accepts a fresh action here. Each approval is single-use. |
| `moonraker_file_delete` | high | policy | `filename` | DESTRUCTIVE: delete a file from the 'gcodes' root. The first call returns an approval prompt; a second call to moonraker_confirm_action with the approval id, confirmation phrase, and acknowledge=true is required. Configuration files cannot be deleted. |
| `moonraker_firmware_restart` | high | policy | `—` | DESTRUCTIVE: perform a complete Klipper firmware restart, resetting Klippy and connected MCUs. An active print will fail. Requires double confirmation. |
| `moonraker_job_queue_remove` | high | policy | `job_ids, all` | DESTRUCTIVE: remove one or more jobs from the queue, or clear the entire queue with all=true. Requires double confirmation through moonraker_confirm_action. |
| `moonraker_klipper_restart` | high | policy | `—` | DESTRUCTIVE: perform a Klipper host restart (reload configuration and restart Klippy). MCUs are not reset. An active print will fail. Requires double confirmation. |
| `moonraker_print_cancel` | high | policy | `—` | DESTRUCTIVE: cancel the active or paused print. This cannot be undone; the part will be incomplete. Requires double confirmation through moonraker_confirm_action. |
| `moonraker_print_start` | high | policy | `filename` | DESTRUCTIVE: start printing a G-code file from the 'gcodes' root. The file must exist. This can heat the printer and move all axes, so it requires double confirmation: the first call returns an approval prompt, then call moonraker_confirm_action with the approval id, phrase, and acknowledge=true. |
| `moonraker_run_macro` | high | policy | `name, params` | DESTRUCTIVE: execute a loaded `gcode_macro` by name, with optional parameters (for example BED=110). Macros can perform arbitrary actions (including heating and motion), so this always requires double confirmation. The first call returns an approval prompt; call moonraker_confirm_action to execute. |
| `moonraker_emergency_stop` | critical | emergency | `—` | IMMEDIATE SAFETY ACTION: halt the printer now and put Klipper into the shutdown state. This bypasses read-only mode and approval prompts by design. Use it when something is going wrong physically. |
| `moonraker_host_reboot` | critical | policy | `—` | ADMIN: reboot the machine running Moonraker/Klipper. The printer will be unavailable while it boots. Requires host administration and double confirmation. |
| `moonraker_host_shutdown` | critical | policy | `—` | ADMIN: shut down the machine running Moonraker/Klipper. It will need manual power-on or Wake-on-LAN. Requires host administration and double confirmation. |
| `moonraker_raw_gcode` | critical | policy | `script` | CRITICAL: execute arbitrary Klipper G-code. Disabled by default (MCP_MOONRAKER_ALLOW_RAW_GCODE=false). When enabled, every call requires double confirmation. Prefer the structured motion/heater tools; they validate against live printer state. |
| `moonraker_service_restart` | critical | policy | `service` | ADMIN: restart a system service managed by Moonraker (for example 'klipper' or 'moonraker'). Requires host administration and double confirmation. |
| `moonraker_update_refresh` | critical | policy | `name` | ADMIN: ask Moonraker's update manager to refresh version information. Requires host administration to be enabled and double confirmation. |
| `moonraker_update_upgrade` | critical | policy | `name` | ADMIN: upgrade one named component through Moonraker's update manager. This can restart services and may require a Klipper restart. Requires host administration and double confirmation. A component name is mandatory to avoid accidental blanket upgrades. |
