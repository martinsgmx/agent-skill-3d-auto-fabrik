# Safety & approval protocol

Both servers implement the same pattern: **prepare → human approval →
confirm**. The agent never self-approves. This file is the deep-dive; SKILL.md
has the short version.

## Risk tiers (as reported by the servers)

| Tier | Meaning | Examples |
| --- | --- | --- |
| `read` | No mutation, no side effects | status, temperatures, inspect, list |
| `low` | Trivially reversible | fan, flow factor, import, queue add |
| `medium` | Real effect, reversible, no approval | slice, heater, move axis, pause/resume |
| `high` | Destructive or irreversible — double confirmation | print start/cancel, export, delete, macros, Klipper restart |
| `critical` | Machine/host admin — off by default | raw G-code, host reboot/shutdown, updates, emergency stop (emergency gate) |

## Gates (who authorizes)

| Gate | Meaning |
| --- | --- |
| `policy` | Allowed/denied by the local safety policy (read-only, temp caps…) |
| `local` | Local info only (policy info, pending approvals, server info) |
| `confirm` | Double confirmation: prepare + confirm |
| `emergency` | Emergency only — `moonraker_emergency_stop`; bypasses prompts by design |

## Approval modes (`[approval] mode`)

- **`in_band`** — the prepare response carries a single-use confirmation
  phrase, shown to the agent/user in chat. The user reads it and says "go";
  the agent calls `*_confirm_action` with that phrase and `acknowledge=true`.
- **`out_of_band`** — no phrase is usable in chat. A human runs
  `mcp-moonraker approve <approval_id>` (or `deny`) in their own terminal.
  The agent waits for the human to report completion, then confirms.
- **`both`** — phrase *and* out-of-band human approval. Recommended for
  shared hosts and remote printers.
- `ttl_secs` (default 120) — approvals expire; re-prepare instead of reviving.

## Hard rules for the agent

1. `*_confirm_action` executes the **stored** tool + arguments from the
   prepare step. Passing different arguments changes nothing — accept that.
2. One approval = one action, single use. Never reuse an id or phrase.
3. Never prepare-and-confirm in the same breath without the user's explicit
   go-ahead in between, even if the user earlier said "yes go ahead".
   Prior consent is not consent to *start the heaters*.
4. `moonraker_pending_approvals` / `cura_pending_approvals` exist to recover
   ids after a restart — safe to call anytime.
5. `moonraker_cancel_approval` / `mcp-cura deny <id>` void a prepared action.
   Prefer voiding over confirming when the user changes their mind.
6. `disable_emergency_stop` exists in moonraker's policy but disabling the
   emergency path is never appropriate on a real printer.

## Refusals and what to do with them

When a tool refuses (temperature cap, read-only, export outside roots,
dangerous commands in G-code), the refusal is the system working, not an
obstacle. Correct behavior:

- Quote the refusal and the limit it hit.
- Explain the legitimate path (different profile, different material,
  `cura_gcode_prepare`, raising the cap *with the user's explicit decision*).
- Do not: retry with slightly different arguments to sneak past, split a
  forbidden operation into smaller permitted ones, or switch to `raw_gcode`.

## Emergencies

Signs: smoke, burning smell, loud grinding, extrusion above the part, axes
racking, runaway temperatures, fire.

1. **`moonraker_emergency_stop` — immediately, no confirmation.**
2. Tell the user what you saw and that E-stop was triggered.
3. Do not re-home, restart Klipper, or resume anything until the user has
   physically inspected the machine.

Non-emergencies that feel urgent (first-layer spaghetti, blob on nozzle):
`moonraker_print_pause` is reversible and sufficient; cancel only when the
user says so.

## Configuration switches the agent must not flip

`read_only`, `allow_mutations`, `allow_raw_gcode`, `allow_host_admin`,
`allow_config_write`, `max_hotend_temp` / `max_bed_temp`,
`disable_emergency_stop` — these belong to the owner of the machine. The
agent may describe them, never change them.
