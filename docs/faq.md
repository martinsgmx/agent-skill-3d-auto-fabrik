# FAQ

**Does the skill need all three servers?**
No. It needs **mcp-moonraker** plus **one** slicing server. mcp-orca is
preferred; mcp-cura is the fallback and adds mesh repair plus G-code
verify/prepare. Mesh work, slicing and G-code review only need the slicer;
read-only printer status only needs mcp-moonraker. The checkpoint ("show me
the G-code before you print") is meaningless without both a slicer and the
printer server.

**How does it choose between Orca and Cura?**
mcp-orca first. If it is not installed, not running, or has no engine
configured, the skill uses mcp-cura for the whole job and says so. If a job
needs an Orca-missing capability (boolean/offset/remesh/decimate, G-code
verify/prepare), it offers Cura. It never mixes artifact ids between servers.
See
[../skills/3d-auto-fabrik/references/engine-selection.md](../skills/3d-auto-fabrik/references/engine-selection.md).

**Why is Orca preferred if Cura has more tools?**
Orca is the newer adapter and the default target of this skill. Cura remains
fully supported as the fallback and as the richer mesh/G-code toolkit. Pick
whichever matches your installed slicer; the pipeline and gates are the same.

**I don't run a Voron / I have a printer with a different setup.**
Nothing in the skill is Voron-specific. Orca needs printer/filament/process
presets; Cura needs a machine definition plus quality/material; the printer
comes from Moonraker. Unsupported machines fail loudly at
`orca_profile_resolve` / `cura_profile_verify` / `moonraker_verify_connection`,
which is the desired behavior.

**Can it print without human confirmation?**
No. `moonraker_print_start` is high risk and always requires approval. With
`mode = "out_of_band"` the human approves in a terminal, out of band; with
`in_band` the approval is presented in chat. Either way the agent may not
self-approve. If you want full autonomy, you must also accept that no software
in this stack will bless an unattended print *on your behalf* — you can of
course write your own wrapper, but that is outside this skill's guarantee and
you should not.

**Why doesn't the slicer upload the G-code itself?**
The slicers do not talk to printers by design. The skill uses Moonraker's
`moonraker_file_upload` for the hand-off: it sends base64 G-code into the
printer's `gcodes` root, then `moonraker_file_verify` checks the SHA-256 and
size, and `moonraker_print_preflight` checks readiness. Uploading never
starts a print. If the upload tool is unavailable or policy refuses it, the
skill reports that; it does not invent another upload tool or call a raw HTTP
endpoint behind your back.

**Orca has no `gcode_verify`. Is that safe?**
The skill compensates: `orca_gcode_inspect` for time/filament/temperature
maxima, `orca_artifact_read_text` for the header/footer, and a hard rule to
re-slice if the end sequence is wrong. Cura's verify/prepare remains
available if you need that extra check — run the job in Cura, or switch
before slicing.

**Tool X isn't showing up.**
Check in this order: server on PATH → client tool filter (OpenCode
permissions, Claude allow/deny, Gemini `includeTools`) → server policy
(`moonraker_policy_info` / `orca_policy_info` / `cura_policy_info`) →
transport (stdio vs HTTP, token). See
[platforms.md](platforms.md#client-side-tool-filtering-read-this-if-a-tool-doesnt-exist).

**Which model should I run the skill on?**
Any capable agentic model with tool use. The skill's value is procedural,
not cleverness-dependent; weaker models benefit most from the explicit gates.

**Does this work with OctoPrint?**
No. mcp-moonraker targets Moonraker/Klipper. For OctoPrint there are
separate MCP servers; this skill's pipeline stages 0–5 (mesh → G-code)
apply unchanged, but Stage 6–7 differ.

**Can I run the servers over HTTP instead of stdio?**
Yes — all three speak streamable HTTP behind a bearer token. Keep the default
loopback bind; never expose them to a network without `allowed_hosts`,
`allowed_origins` and a token. Remote print control is exactly the scenario
`out_of_band`/`both` approval mode exists for.

**How do I know the versions match?**
`mcp-orca --version`, `mcp-cura --version`, `mcp-moonraker --version`, then
regenerate the reference tables with
`python3 scripts/generate-tool-reference.py` — the generated tables carry the
version in the provenance line when you commit the result.

**Why MIT?**
The skill is MIT. The companion servers keep their own licenses: mcp-orca is
Apache-2.0; mcp-cura and mcp-moonraker are MIT. The human running the printer
gets maximum freedom; the author accepts no liability — see
[../LICENSE](../LICENSE) and [safety.md](safety.md).
