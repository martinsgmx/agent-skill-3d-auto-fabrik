# FAQ

**Does the skill need both servers?**
Yes, for the full pipeline. Mesh work, slicing and G-code review only need
mcp-cura; read-only printer status only needs mcp-moonraker. The skill's
checkpoint ("show me the G-code before you print") is meaningless without
both.

**I don't run a Voron / I have a printer with a different setup.**
Nothing in the skill is Voron-specific. The machine definition, quality
profiles and material come from your Cura installation; the printer comes
from Moonraker. Unsupported machines fail loudly at
`cura_profile_verify` / `moonraker_verify_connection`, which is the desired
behavior.

**Can it print without human confirmation?**
No. `moonraker_print_start` is high risk and always double-confirmed. With
`mode = "out_of_band"` the human approves in a terminal, out of band; with
`in_band` the confirmation phrase is presented in chat. Either way the agent
may not self-approve. If you want full autonomy, you must also accept that
no software in this stack will bless an unattended print *on your behalf* —
you can of course write your own wrapper, but that is outside this skill's
guarantee and you should not.

**Why doesn't it upload the G-code to the printer itself?**
Neither server ships an upload tool on purpose: the hand-off is an
approval-gated export or a human copy. If you want a one-click experience,
map the gcodes root onto a directory under mcp-cura's export roots (e.g.
a CIFS/NFS mount on the printer running OctoPrint-style shares) — then
Stage 6 is `cura_artifact_export` with the user's approval.

**Tool X isn't showing up.**
Check in this order: server on PATH → client tool filter (OpenCode
permissions, Claude allow/deny, Gemini `includeTools`) → server policy
(`moonraker_policy_info` / `cura_policy_info`) → transport (stdio vs HTTP,
token). See [platforms.md](platforms.md#client-side-tool-filtering-read-this-if-a-tool-doesnt-exist).

**Which model should I run the skill on?**
Any capable agentic model with tool use. The skill's value is procedural,
not cleverness-dependent; weaker models benefit most from the
explicit gates.

**Does this work with OctoPrint?**
No. mcp-moonraker targets Moonraker/Klipper. For OctoPrint there are
separate MCP servers; this skill's pipeline stages 0–5 (mesh → G-code)
apply unchanged, but Stage 6–7 differ.

**Can I run the servers over HTTP instead of stdio?**
Yes — both speak streamable HTTP behind a bearer token. Keep the default
loopback bind; never expose them to a network without `allowed_hosts`,
`allowed_origins` and a token. Remote print control is exactly the scenario
`out_of_band`/`both` approval mode exists for.

**How do I know the versions match?**
`mcp-cura --version` / `mcp-moonraker --version`, then regenerate the
reference tables with `python3 scripts/generate-tool-reference.py` — the
generated tables carry the version in the provenance line when you commit
the result.

**Why MIT?**
Same license as both companion MCP servers. The human running the printer
gets maximum freedom; the author accepts no liability — see
[../LICENSE](../LICENSE) and [safety.md](safety.md).
