# Configuration

Both servers follow the same layering:

```text
built-in defaults  <  TOML file  <  environment variables  <  CLI flags
```

Generate the fully documented starter files with `mcp-cura init` and
`mcp-moonraker init` (`-o -` prints to stdout). **Never put secrets in the
TOML** — both servers read secrets from the environment. `print-config` shows
the fully resolved, secret-free configuration; use it instead of guessing.

Defaults locations:

| Item | mcp-cura | mcp-moonraker |
| --- | --- | --- |
| Config file | `~/.config/mcp-cura/mcp-cura.toml` | `~/.config/mcp-moonraker/mcp-moonraker.toml` |
| Config env override | `MCP_CURA_CONFIG` | `MCP_MOONRAKER_CONFIG` |
| State / workspace | `~/.local/share/mcp-cura` | `~/.local/state/mcp-moonraker` |
| Override state dir TOML | `[workspace] root`, `[approval] state_dir` | `[approval] state_dir` |

## mcp-cura

### `[server]`

| Key | Default | Meaning |
| --- | --- | --- |
| `transport` | `stdio` | `stdio` for local agents; `http` for streamable HTTP |
| `http.host` / `http.port` | `127.0.0.1` / `8765` | bind address |
| `http.path` | `/mcp` | endpoint path |
| `http.allowed_hosts` / `allowed_origins` | `[]` | required when binding off loopback |
| `http.allow_unauthenticated` | `false` | never set this off-loopback |
| `http.token` via env | `MCP_CURA_HTTP_TOKEN` | bearer token for HTTP |

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
| `MCP_CURA_CONFIG` / `MCP_MOONRAKER_CONFIG` | both | TOML path override |
| `MCP_CURA_HTTP_TOKEN` / `MCP_MOONRAKER_HTTP_TOKEN` | both | HTTP transport bearer token |
| `MOONRAKER_URL` | moonraker | Moonraker endpoint |
| `MOONRAKER_API_KEY` | moonraker | Moonraker API key, if configured |
| `MCP_CURA_ENGINE_BINARY` | cura | engine binary path |
| `MCP_MOONRAKER_ALLOW_RAW_GCODE` | moonraker | set `true` to enable raw G-code (not recommended) |

## Hardening recipes

**Read-only demo / evaluation agent** — in both TOML files:

```toml
[policy]
read_only = true
```

**Autonomous agent with mechanical actions but no prints** —
mutations on, but print start still needs double confirmation (it always
does). Keep `allow_raw_gcode = false`.

**Untrusted or remote agent** — `mode = "both"`, `ttl_secs = 60`, export root
mapped to a drop directory the printer does *not* watch, and `read_only` on
the printer host account.
