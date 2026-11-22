# Safety

3D printers are heaters, motors, belts and nozzles moving near flammable
plastic. The software here has real blast radius; the safety model of this
project is therefore **defense in depth**, not politeness text in a prompt.

## The three layers

1. **Server-side policy** — the MCP servers cap temperatures, disable raw
   G-code and host administration by default, confine imports/exports to
   configured roots, and gate destructive tools behind approval. Policy lives
   in the servers; it cannot be argued out of by a persuasive prompt.
2. **Approval lifecycle** — a prepared action becomes a single-use, expiring
   approval. mcp-orca stores the request and asks you to decide then retry
   the identical call; mcp-cura and mcp-moonraker use a phrase plus
   `*_confirm_action`. The executed action is always the prepared action.
3. **The skill** — procedural discipline: choose an engine and stick to it,
   inspect the mesh, resolve the profile, review the G-code, verify the
   connection and the transferred file, present every approval prompt
   verbatim, stop at the human checkpoint, and treat `emergency_stop` as the
   single, unmistakable exception.

## Risk ladder

| Tier | Reversible? | Examples | Gate |
| --- | --- | --- | --- |
| read | n/a | status, temps, inspect, lists, profile resolve | none (policy) |
| low | yes | fan %, flow/speed factor, imports, mesh transform, queue add | none (policy) |
| medium | mostly | slice, heaters, XY jog, pause/resume, approval decision | none (policy) — but announce first |
| high | no | print start/cancel, exports, deletes, macros, Klipper restarts | approval required |
| critical | no | raw G-code, host reboot/shutdown, updates | approval + explicit policy opt-in |
| emergency | — | `moonraker_emergency_stop` | always available; physical danger only |

mcp-orca stops at `high`; it never touches the printer. The `critical` tier
belongs to mcp-cura/mcp-moonraker host administration.

## G-code review is not optional

This is the gate that stands between a bad slice and a bad print.

- **mcp-cura** has `cura_gcode_verify`: dangerous commands, temperatures vs.
  local policy, missing heater shutdown, missing stepper disable, missing
  metadata. Fix a missing shutdown with `cura_gcode_prepare`; re-slice for
  dangerous commands.
- **mcp-orca** has `orca_gcode_inspect` only. It reports statistics and
  maximum temperatures, but **does not scan for dangerous commands**. The
  agent must read the header and footer with `orca_artifact_read_text` and
  confirm heater-off, park/lift, `M84`, and the absence of unexpected
  `M112`/`M502`/`M500`/mid-file `G28`. If the end sequence is wrong, re-slice
  with a corrected process preset. There is no Orca prepare/rewrite tool.

Never hand-edit G-code to "fix" a safety issue. Re-slice.

## Standing rules (short form)

- **First layer is king.** Watch it or tell the user to watch it. Most
  field failures look fine at minute 1 and wrong by minute 5.
- **Pause, don't cancel.** `print_pause` → inspect → `print_resume` is
  almost always the right move; `print_cancel` destroys the job and
  requires explicit confirmation anyway.
- **E-stop is not "stop the print".** It is "halt the machine now". Use it
  for fire/grinding/ramming. For everything else, pause.
- **Never widen scope to finish a task.** If you hit the export root wall,
  the temp cap, raw G-code being disabled — stop and surface it, even if the
  user "seemed to want it done".
- **One approval, one action, one time.** TTL is deliberately short;
  stale approvals are re-prepared, not revived.
- **One engine per job.** Do not pass Orca artifact ids to Cura or vice
  versa; switching means re-importing.
- **Supervision is a requirement, not a courtesy.** Remote, unattended
  printing is possible with this stack; it is enabled by `out_of_band`
  approval mode and camera checks — but it remains the user's call, and
  the agent should say so when leaving a printer alone.

## What to do when something is wrong mid-print

| Symptom | Action |
| --- | --- |
| Spaghetti / detached print | `moonraker_print_pause`; report; user decides |
| Nozzle clog / under-extrusion | pause; report; user decides |
| Layer shift | pause; report; camera snapshot for evidence |
| Thermal runaway / shutdown state | **stop touching the tools**; report; physical inspection; no restarts without explicit ask |
| Smoke / fire | `moonraker_emergency_stop` immediately, then phone call / fire safety, then report |
| Power loss | wait; `verify_connection` after power returns; do not auto-restart Klipper if Klipper reports `shutdown` |

## Reporting a safety fault

If you find a way past a gate — an approval that replays wrong arguments, an
export outside its root, a temperature cap bypassed — that is a **critical
security vulnerability**: see [SECURITY.md](../SECURITY.md). Do not open a
public issue.
