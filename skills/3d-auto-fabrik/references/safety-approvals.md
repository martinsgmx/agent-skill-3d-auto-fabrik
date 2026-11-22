# Safety & approval protocol

All three servers share one idea: **the server decides, the human authorizes,
the agent relays**. The agent never self-approves. This file is the deep-dive;
SKILL.md has the short version.

## Risk tiers (as reported by the servers)

| Tier | Meaning | Examples |
| --- | --- | --- |
| `read` | No mutation, no side effects | status, temperatures, inspect, list, profile resolve |
| `low` | Trivially reversible | fan, flow factor, import, mesh transform/merge, queue add |
| `medium` | Real effect, reversible, no approval | slice, heater, move axis, pause/resume, approval decision |
| `high` | Destructive or irreversible — approval required | print start/cancel, export, delete, macros, Klipper restart |
| `critical` | Machine/host admin — off by default | raw G-code, host reboot/shutdown, updates, emergency stop (emergency gate) |

mcp-orca tops out at `high`; it never touches hardware. mcp-cura and
mcp-moonraker add the `critical` host-admin tier.

## Gates (who authorizes)

| Gate | Meaning |
| --- | --- |
| `policy` | Allowed/denied by the local safety policy (read-only, temp caps, roots…) |
| `local` | Local info only (policy info, pending approvals, server info) |
| `confirm` | Double confirmation: prepare + confirm (Cura, Moonraker) |
| `emergency` | Emergency only — `moonraker_emergency_stop`; bypasses prompts by design |

## Two approval protocols — do not mix them

### mcp-orca: pending request → decide → retry

1. The first gated call does **not** execute. It fails with a pending
   `apr_…` id and a reason.
2. The user approves in chat, or runs `mcp-orca approvals approve <id>` on the
   host when `approval.mode = "out_of_band"`.
3. In `in_band` / `both`, the agent then calls
   `orca_approval_decide(approval_id, approve=true)`. In `out_of_band` the
   server refuses that call — wait for the human to run the CLI.
4. Retry the **identical** tool call within `approval.ttl_secs`. The approval
   is consumed exactly once. Changed arguments are a different action and
   need a new approval.

There is no `orca_confirm_action`. Do not invent one, and do not treat
`orca_approval_decide` as permission to change the prepared arguments.

### mcp-cura and mcp-moonraker: prepare → phrase → confirm

1. The first gated call returns an `approval_id` and, in in-band mode, a
   single-use confirmation phrase.
2. Show the prompt verbatim and wait for the user.
3. Call `cura_confirm_action` / `moonraker_confirm_action` with the id, the
   phrase and `acknowledge=true`. The stored tool + arguments execute;
   arguments passed to confirm are decorative.
4. `mcp-cura deny <id>` / `mcp-moonraker approve|deny <id>` work out of band.

## Approval modes (`[approval] mode`)

- **`in_band`** — the agent may complete the approval after the user says yes
  in chat. Phrase-based servers show the phrase; Orca shows the request id.
- **`out_of_band`** — no decision is accepted over MCP. A human runs the
  server's CLI (`mcp-orca approvals approve|deny`, `mcp-cura approve|deny`,
  `mcp-moonraker approve|deny`). The agent waits for the human to report
  completion.
- **`both`** — phrase/decision *and* out-of-band human approval. Recommended
  for shared hosts and remote printers.
- `ttl_secs` (default 120) — approvals expire; re-prepare instead of reviving.

## Hard rules for the agent

1. One approval = one action, single use. Never reuse an id or phrase.
2. Never prepare-and-complete in the same breath without the user's explicit
   go-ahead in between, even if the user earlier said "yes go ahead". Prior
   consent is not consent to *start the heaters*.
3. `*_pending_approvals` exists to recover ids after a restart — safe to call
   anytime.
4. Prefer voiding over completing when the user changes their mind:
   `moonraker_cancel_approval`, `mcp-orca approvals deny <id>`,
   `mcp-cura deny <id>`.
5. `disable_emergency_stop` exists in Moonraker's policy but disabling the
   emergency path is never appropriate on a real printer.

## Refusals and what to do with them

When a tool refuses (temperature cap, read-only, export outside roots, missing
presets, dangerous commands in G-code), the refusal is the system working,
not an obstacle. Correct behavior:

- Quote the refusal and the limit it hit.
- Explain the legitimate path (different profile/material, `data` import,
  `cura_gcode_prepare`, raising a cap *with the user's explicit decision*).
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
`allow_config_write`, `allow_slicing`, `allow_export`, `allow_delete`,
`workspace.import_roots` / `export_roots`, `engine.preset` /
`slice_command`, `max_hotend_temp` / `max_bed_temp`,
`disable_emergency_stop` — these belong to the owner of the machine. The
agent may describe them, never change them.
