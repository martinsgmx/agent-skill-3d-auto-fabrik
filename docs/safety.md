# Safety

3D printers are heaters, motors, belts and nozzles moving near flammable
plastic. The software here has real blast radius; the safety model of this
project is therefore **defense in depth**, not politeness text in a prompt.

## The three layers

1. **Server-side policy** — the MCP servers cap temperatures, disable raw
   G-code and host administration by default, refuse exports outside the
   configured roots, and gate destructive tools behind double confirmation.
   Policy lives in the servers; it cannot be argued out of by a persuasive
   prompt.
2. **Approval lifecycle** — prepare → single-use, expiring approval id →
   confirm. The executed action is the prepared action, not whatever the
   confirm-call says. Approvals are local state files with restricted
   permissions (`in_band` / `out_of_band` / `both`).
3. **The skill** — procedural discipline: verify before you trust
   (`cura_gcode_verify`, `moonraker_verify_connection`, file metadata after
   transfer), present every approval prompt verbatim, stop at the human
   checkpoint, and treat `emergency_stop` as the single, unmistakable
   exception.

## Risk ladder

| Tier | Reversible? | Examples | Gate |
| --- | --- | --- | --- |
| read | n/a | status, temps, inspect, lists | none (policy) |
| low | yes | fan %, flow/speed factor, imports, queue add | none (policy) |
| medium | mostly | slice, heaters, XY jog, pause/resume | none (policy) — but announce first |
| high | no | print start/cancel, exports, deletes, macros, Klipper restarts | double confirmation |
| critical | no | raw G-code, host reboot/shutdown, updates | double confirmation + explicit policy opt-in |
| emergency | — | `moonraker_emergency_stop` | always available; physical danger only |

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
