# Choosing an engine: mcp-orca vs mcp-cura

Both slicers implement the same contract — content-addressed artifacts,
background slice jobs, policy gates, no printer contact. Pick one for the
whole job. The pipeline stages are identical; only the tool names and profile
model differ.

## Decision order

1. **mcp-orca**, if it responds and has an engine configured: `orca_engine_info`
   reports `available: true` **and** `slice_command_configured: true`
   (`engine.preset = "orca"` or `engine.slice_command`). A found binary with
   `slice_command_configured: false` is not enough — slicing will fail.
2. **mcp-cura**, if mcp-orca is missing, fails to start, or has no engine.
3. Stop and report if neither works.

Use `mcp-orca doctor` / `mcp-cura doctor` (CLI) or `orca_doctor` plus
`orca_engine_info` (MCP) before importing. Say the chosen engine in one line;
silent fallback is confusing when the user expects Orca output.

## Capability matrix

| Capability | mcp-orca | mcp-cura |
| --- | --- | --- |
| Import (path / base64) | yes; import roots default empty | yes; default Downloads/Documents/Desktop/`~/models` |
| Mesh inspect (STL/OBJ) | yes | yes (STL/3MF) |
| Transform (translate/rotate/scale/mirror) | yes | yes + `center_on_bed` |
| Merge (triangle soup) | yes | yes |
| Boolean union/subtract/intersect | **no** | yes |
| Offset / remesh / decimate | **no** | yes |
| Profile discovery | printer/filament/process native `.json` presets | definitions/quality/material/variant/intent |
| Profile resolve | yes (by reference + workspace overrides) | yes (merged settings map) |
| Profile verify | **no** | yes |
| Slice | yes (`engine.preset = "orca"` or `slice_command`) | yes (CuraEngine) |
| G-code inspect | yes (stats; **no dangerous-command scan**) | yes |
| G-code verify | **no** | yes |
| G-code prepare/rewrite | **no** | yes |
| Export / delete | approval via `orca_approval_decide` + retry | prepare + `cura_confirm_action` |

If a job needs a capability Orca does not have, do not fake it. Tell the user
what is missing and offer Cura. Restart at Stage 1 in Cura — see below.

## Profile model differences

**Orca** presets are three native `.json` files:

- `printer` — machine limits, nozzle, build volume.
- `filament` — material temperatures, cooling, flow.
- `process` — layer height, walls, infill, speeds, supports.

`orca_profile_resolve` requires all three (or a supported project). It returns
`resolution[]` entries showing whether each selection resolved to a discovered
preset, an explicit path, or a workspace artifact. Native presets are resolved
*by reference*; their settings are not copied into `effective_settings`.
`settings_complete: false` is therefore normal and is not an error. The final
G-code is the authoritative check on temperatures.

Workspace profiles (`orca_profile_create` / `orca_profile_update`) carry a
`base_profile` pointing at a native preset plus a `settings` object. They are
merged last and are the right place for repeatable overrides (for example a
capped nozzle temperature). They never mutate the user's Orca installation.

**Cura** profiles use a definition plus quality/material/variant/intent
layers. `cura_profile_resolve` merges them into one settings map and
`cura_profile_verify` checks machine dimensions, temperatures, layer height,
line width and speed before slicing. Zero errors is the bar.

## Artifact ids do not cross servers

Every server has its own content-addressed workspace. An `art_…` id from
mcp-orca is meaningless to mcp-cura, and vice versa.

If you must switch engines mid-job:

1. Export the model artifact from the current server (`*_artifact_export` to a
   configured export root), or re-read the original file.
2. Import it into the other server (`*_artifact_import`).
3. Restart the pipeline at Stage 2 with the new id.

Never pass a foreign id to a tool and never claim the same artifact exists in
both stores. The exported G-code is the only thing that needs to reach the
printer; its provenance stays with the slicer that produced it.

## Approval differences that matter

- **mcp-orca**: the first gated call *fails* with a pending `apr_…` id. Decide
  with `orca_approval_decide` (when `approval.mode` is `in_band` or `both`) or
  `mcp-orca approvals approve <id>` on the host (`out_of_band`). Then retry the
  identical call; the approval is consumed once. There is no
  `orca_confirm_action`.
- **mcp-cura** and **mcp-moonraker**: prepare returns an id and, in in-band
  mode, a single-use phrase. The human approves, then the agent calls
  `*_confirm_action` with the phrase and `acknowledge=true`.

Do not translate one protocol into the other. Use the server's own tools.

## Fallback dialogue (short)

> **User:** Slice bracket.stl for the Voron in PETG.
> **Agent:** mcp-orca is installed but has no engine configured
> (`engine.preset` unset, `slice_command` empty), so I'll use mcp-cura for
> this job. Same pipeline, CuraEngine output. Importing now…

If the user explicitly wants Orca, stop and help them configure
`engine.preset = "orca"` and a reachable `orca-slicer` binary rather than
silently switching.
