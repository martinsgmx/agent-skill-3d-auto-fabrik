# Configuration

All three servers follow the same layering:

```text
built-in defaults  <  TOML file  <  environment variables  <  CLI flags
```

Generate the fully documented starter files with
`mcp-orca init --output mcp-orca.toml` and
`mcp-cura init -o -` / `mcp-moonraker init -o -` (the latter two print to
stdout with `-o -`). **Never put secrets in the TOML** — the servers read
secrets from the environment. `print-config` shows the fully resolved,
secret-free configuration; use it instead of guessing.

Default locations:

| Item | mcp-orca | mcp-cura | mcp-moonraker |
| --- | --- | --- | --- |
| Config file | via `--config` / `MCP_ORCA_CONFIG` (no implicit file; example `~/.config/mcp-orca/mcp-orca.toml`) | `~/.config/mcp-cura/mcp-cura.toml` | `~/.config/mcp-moonraker/mcp-moonraker.toml` |
| Config env override | `MCP_ORCA_CONFIG` | `MCP_CURA_CONFIG` | `MCP_MOONRAKER_CONFIG` |
| State / workspace | `~/.local/share/mcp-orca` | `~/.local/share/mcp-cura` | `~/.local/state/mcp-moonraker` |

## mcp-orca

### `[server]`

| Key | Default | Meaning |
| --- | --- | --- |
| `transport` | `stdio` | `stdio` for local agents; `http` for streamable HTTP |
| `http.host` / `http.port` | `127.0.0.1` / `8765` | bind address |
| `http.path` | `/mcp` | endpoint path |
| `http.allow_unauthenticated` | `false` | never set this off-loopback |
| `http.token` via env | `MCP_ORCA_HTTP_TOKEN` | bearer token for HTTP |

### `[workspace]`

| Key | Default | Meaning |
| --- | --- | --- |
| `root` | `~/.local/share/mcp-orca` | content-addressed artifact/job store |
| `import_roots` | **`[]`** | absolute paths allowed for `path` imports; empty disables them |
| `export_roots` | **`[]`** | absolute paths allowed for exports; empty disables them |
| `max_import_bytes` | 512 MB | base64/import size cap |
| `max_artifact_bytes` | 1 GB | artifact size cap |
| `max_artifacts` | 10000 | retention cap |
| `keep_jobs` | 100 | job-record retention |

Path imports and exports are **off by default**. That is deliberate: the
agent uses the base64 `data` channel for imports, and the user either adds an
export root or copies the G-code themselves. Do not widen these roots just to
make one job pass — ask the owner.

### `[engine]`

| Key | Default | Meaning |
| --- | --- | --- |
| `runner` | `binary` | `binary` (host CLI) or `docker` |
| `preset` | unset | `orca` enables the built-in OrcaSlicer CLI contract |
| `binary` | `orca-slicer` | host executable (name or absolute path) |
| `docker_image` | unset | image for the Docker runner |
| `docker_command` | `[]` | optional custom Docker argv |
| `slice_command` | `[]` | custom argv template; **overrides** the preset |
| `env` | `{}` | extra environment for the slicer process |
| `timeout_secs` | 900 | per-job timeout |
| `max_concurrent_jobs` | 2 | job concurrency |

Slicing is disabled until either `preset = "orca"` or a non-empty
`slice_command` is configured **and** the binary/image is reachable. The
built-in preset stages the model(s) and native preset JSONs into the job
directory, passes `--load-settings "process.json;printer.json"`,
`--load-filaments filament.json`, merged `--key=value` overrides, `--arrange
1`, `--slice 0`, `--outputdir {jobdir}`, and collects `plate_N.gcode` into
`output.gcode`.

`slice_command` placeholders: `{binary}`, `{image}`, `{jobdir}`, `{gcode}`,
`{models}`, `{model}`, `{printer}`, `{filament}`, `{process}`, `{project}`,
`{overrides}`, `{settings}`, `{plan_json}`. `{models}` expands to one argv
entry per model.

### `[profiles]`

| Key | Default | Meaning |
| --- | --- | --- |
| `search_paths` | `[]` | explicit preset directories (bounded scan) |
| `use_os_defaults` | `true` | scan known OrcaSlicer config/resource locations if present |

There is no whole-system crawl. `orca_profile_refresh` rescans. Workspace
custom profiles are stored under the workspace and never mutate the user's
Orca installation.

### `[policy]`

| Key | Default | Meaning |
| --- | --- | --- |
| `read_only` | `false` | when true, every mutation is refused |
| `allow_workspace_writes` | `true` | imports, mesh transforms, custom profiles |
| `allow_slicing` | `true` | `orca_slice` and cancellation |
| `allow_export` | `true` | `orca_artifact_export` (still approval-gated) |
| `allow_delete` | `true` | `orca_artifact_delete` (still approval-gated) |

mcp-orca has no printer temperature caps because it never talks to the
printer. Temperature sanity is checked on the produced G-code against
mcp-moonraker's caps.

### `[approval]`

`mode = "in_band" | "out_of_band" | "both"`, `ttl_secs = 120`. Gated calls
create a pending request; decide with `orca_approval_decide` (in-band/both) or
`mcp-orca approvals approve|deny <id>` (out-of-band), then retry the identical
call.

### Environment variables

`MCP_ORCA_CONFIG`, `MCP_ORCA_TRANSPORT`, `MCP_ORCA_HTTP_HOST`,
`MCP_ORCA_HTTP_PORT`, `MCP_ORCA_HTTP_TOKEN`, `MCP_ORCA_WORKSPACE`,
`MCP_ORCA_ENGINE_RUNNER`, `MCP_ORCA_ENGINE_BINARY`, `MCP_ORCA_DOCKER_IMAGE`,
`MCP_ORCA_LOG_LEVEL`.

## mcp-cura (fallback)

### `[workspace]`

`root`, `import_roots`, `export_roots`, `max_import_bytes` (512 MB),
`max_artifact_bytes` (1 GB), `max_artifacts` (10000), `keep_jobs` (100).
Default import roots: Downloads, Documents, Desktop, `~/models`. Content is
addressed by SHA-256 (`art_<32 hex>`).

### `[engine]`

`runner = "binary" | "docker"`, `binary = "CuraEngine"`, `docker_args = []`,
`search_paths = []`, `timeout_secs = 900`, `max_log_bytes`, `mode =
"resolved_json"`, `verbose = false`. A local CuraEngine binary comes from a
normal Cura installation (e.g. `/usr/lib/cura/CuraEngine`) or from the
AppImage fetch script shipped in the mcp-cura repo
(`scripts/fetch-cura-engine.sh`). The engine is probed with
`cura_engine_info` / `doctor` — it is never modified.

Env: `MCP_CURA_ENGINE_BINARY`, `MCP_CURA_ENGINE_DEFINITIONS`,
`MCP_CURA_ENGINE_RUNNER`, `MCP_CURA_ENGINE_DOCKER_IMAGE` (see the mcp-cura
repo's `docs/configuration.md` for the full matrix — it is authoritative).

### `[profiles]`

`dirs = [...]` (default: `~/.local/share/cura`, `~/.config/cura`),
`auto_discover = true`, `max_profiles = 20000`. `cura_profile_refresh`
rescans. Custom quality-change profiles are written into the workspace.

### `[policy]`

| Key | Default | Meaning |
| --- | --- | --- |
| `read_only` | `false` | when true, every mutation is refused |
| `allow_workspace_writes` / `allow_slicing` / `allow_export` / `allow_delete` | `true` | coarse capability switches |
| `max_hotend_temp` / `max_bed_temp` | `320` / `130` °C | resolved profile temps above this are rejected |
| `max_triangles` | `5000000` | mesh size cap |
| `max_voxel_cells` | `64000000` | boolean/offset/remesh memory cap |
| `max_concurrent_jobs` | `2` | slicing concurrency |
| `max_slice_secs` | `900` | per-job engine timeout |

### `[approval]`

`mode = "in_band" | "out_of_band" | "both"`, `ttl_secs = 120`,
`state_dir = "~/.local/share/mcp-cura/state"`.

For a shared host or an autonomous agent, use `out_of_band` or `both`.

## mcp-moonraker

### `[moonraker]`

| Key | Default | Meaning |
| --- | --- | --- |
| `url` | `http://127.0.0.1:7125` | Moonraker endpoint; override with `MOONRAKER_URL` |
| `timeout_secs` | `15` | per-request timeout |
| `script_timeout_secs` | `120` | G-code script/gcode budget for `printer.gcode.script` |
| `tls_verify` | `true` | set false only with a self-signed printer cert |
| `max_response_bytes` | `8388608` | response cap (8 MB) |

Secret: `MOONRAKER_API_KEY` (only if Moonraker requires one).

### `[policy]`

| Key | Default | Meaning |
| --- | --- | --- |
| `read_only` | `false` | when true, every mutation is refused |
| `allow_mutations` | `true` | heaters, fans, motion, pause/resume |
| `allow_raw_gcode` | **`false`** | arbitrary G-code — leave off |
| `allow_host_admin` | **`false`** | reboot/shutdown/update/service restart — leave off |
| `allow_config_write` | `false` | not implemented in v0.1 |
| `max_hotend_temp` / `max_bed_temp` | `300` / `120` °C | server-side caps |
| `disable_emergency_stop` | `false` | leave false |

### `[approval]`

`mode`, `ttl_secs = 120`, `state_dir = "~/.local/state/mcp-moonraker"` —
same semantics as mcp-cura.

### `[camera]`

`max_bytes` (8 MB), `timeout_secs = 10`, `allow_private_hosts = true`,
`allowed_hosts = []` — restrict camera hosts if the printer can reach other
devices.

## Environment variables worth knowing

| Variable | Server | Purpose |
| --- | --- | --- |
| `MCP_ORCA_CONFIG` / `MCP_CURA_CONFIG` / `MCP_MOONRAKER_CONFIG` | all | TOML path override |
| `MCP_ORCA_HTTP_TOKEN` / `MCP_CURA_HTTP_TOKEN` / `MCP_MOONRAKER_HTTP_TOKEN` | all | HTTP transport bearer token |
| `MOONRAKER_URL` | moonraker | Moonraker endpoint |
| `MOONRAKER_API_KEY` | moonraker | Moonraker API key, if configured |
| `MCP_ORCA_ENGINE_BINARY` | orca | `orca-slicer` path |
| `MCP_ORCA_ENGINE_RUNNER` | orca | `binary` or `docker` |
| `MCP_CURA_ENGINE_BINARY` | cura | CuraEngine path |
| `MCP_MOONRAKER_ALLOW_RAW_GCODE` | moonraker | set `true` to enable raw G-code (not recommended) |

## Skill-level user configuration (3d-auto-fabrik)

The skill reads a small, user-owned preferences file. It is **not** a server
config and it never replaces the three TOML files above.

| File | Purpose |
| --- | --- |
| `~/.config/3d-auto-fabrik/config.yaml` | global labels and preferences |
| `./3d-auto-fabrik.yaml` | optional project-local override |

Contents: `drop_dir` (default `model_downloaded/files`), `temp_root` (default
`${TMPDIR:-/tmp}/3d-auto-fabrik`), `download_max_bytes` (default 512 MB),
named printers and materials mapped to **exact** preset ids, and optional
build-volume facts. Never store tokens or API keys here — secrets stay in the
servers' environment.

Live MCP facts are the source of truth at every preflight: `orca_server_info`
/ `orca_doctor` / `orca_profile_list` (or the Cura equivalents) and read-only
`moonraker_config` / `moonraker_server_info` / `moonraker_policy_info`. The
agent may write this user config only during an explicit onboarding request;
it never edits a slicer TOML, `printer.cfg`, or a server's import/export roots.
See
`skills/3d-auto-fabrik/references/printer-materials.md` for the full model.

## Hardening recipes

**Read-only demo / evaluation agent** — in all three TOML files:

```toml
[policy]
read_only = true
```

**Autonomous agent with mechanical actions but no prints** —
mutations on, but print start still needs approval (it always does). Keep
`allow_raw_gcode = false`.

**Untrusted or remote agent** — `mode = "both"`, `ttl_secs = 60`, export root
mapped to a drop directory the printer does *not* watch, and `read_only` on
the printer host account.

**Orca without a local binary** — use the Docker runner:

```toml
[engine]
runner = "docker"
preset = "orca"
docker_image = "your-orcaslicer-image:tag"
```
