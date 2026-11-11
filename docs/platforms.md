# Platforms & client registration

Two separate registrations per client: (1) the **skill** (instructions), and
(2) the **MCP servers** (tools). Both are shown per client. Paths shown are
Linux/macOS; adjust on Windows.

The skill id is `3d-auto-fabrik`. Install = copy (or symlink)
`skills/3d-auto-fabrik/` into the client's skills directory.

## OpenCode (V2)

Skill — any of:

```text
.opencode/skills/3d-auto-fabrik/SKILL.md     # project
~/.config/opencode/skills/3d-auto-fabrik/    # global
.agents/skills/3d-auto-fabrik/                # project, portable alias
~/.agents/skills/3d-auto-fabrik/              # global, portable alias
```

MCP — `opencode.jsonc` (note: V2 uses `mcp.servers`, not bare `mcp`):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "cura":      { "type": "local", "command": ["mcp-cura"] },
      "moonraker": { "type": "local", "command": ["mcp-moonraker"],
                     "environment": { "MOONRAKER_URL": "http://printer.local:7125" } }
    }
  }
}
```

Or the CLI form: `opencode mcp add cura -- mcp-cura`. `opencode mcp list`
shows connection state; tool names appear as `cura_<tool>` /
`moonraker_<tool>`.

## Claude Code / Claude Desktop

Skill:

```text
.claude/skills/3d-auto-fabrik/SKILL.md   # project
~/.claude/skills/3d-auto-fabrik/         # personal
```

MCP — project `.mcp.json`:

```json
{
  "mcpServers": {
    "cura":      { "command": "mcp-cura" },
    "moonraker": { "command": "mcp-moonraker",
                   "env": { "MOONRAKER_URL": "http://printer.local:7125" } }
  }
}
```

or CLI: `claude mcp add cura -- mcp-cura`. Claude Desktop uses
`claude_desktop_config.json` (`~/.config/Claude/` on Linux,
`~/Library/Application Support/Claude/` on macOS) with the same
`mcpServers` object; use absolute binary paths
(`~/.cargo/bin/mcp-cura`) if the client can't find them.

**Claude.ai (web) cannot launch local stdio binaries.** Use Claude Desktop,
Claude Code, or serve the MCP servers over authenticated streamable HTTP
(`mcp-cura serve --transport http` with `MCP_CURA_HTTP_TOKEN`, mind the
loopback rules) and register the remote URL instead.

## Gemini CLI

Skill (user or workspace tier):

```sh
gemini skills install <this-repo-url> --consent --path skills/3d-auto-fabrik
# or: cp -r skills/3d-auto-fabrik ~/.agents/skills/   (portable alias)
# or: cp -r skills/3d-auto-fabrik .gemini/skills/     (workspace)
/skills list
```

MCP — `~/.gemini/settings.json` (user) or `.gemini/settings.json` (project),
or the CLI:

```sh
gemini mcp add cura mcp-cura
gemini mcp add moonraker mcp-moonraker -e MOONRAKER_URL=http://printer.local:7125
```

```json
{
  "mcpServers": {
    "cura":      { "command": "mcp-cura" },
    "moonraker": { "command": "mcp-moonraker",
                   "env": { "MOONRAKER_URL": "http://printer.local:7125" } }
  }
}
```

Tool names appear as `cura_<tool>` / `moonraker_<tool>` (Gemini may prefix
with `serverName__toolName` on conflicts).

## Cursor

MCP — `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{ "mcpServers": {
    "cura":      { "command": "mcp-cura" },
    "moonraker": { "command": "mcp-moonraker" }
} }
```

Skill — Cursor discovers Agent Skills from `~/.cursor/skills/` and
`.agents/skills/`; if your build doesn't, put the SKILL.md content into a
`.cursor/rules/3d-auto-fabrik.mdc` rule with `alwaysApply: false` and keep
`references/` next to the repo. See
<https://cursor.com/docs> for the current rules/skills split.

## Windsurf

MCP — `~/.codeium/windsurf/mcp_config.json`:

```json
{ "mcpServers": {
    "cura":      { "command": "mcp-cura" },
    "moonraker": { "command": "mcp-moonraker" }
} }
```

Skill — Windsurf uses rules under `.windsurf/rules/`. Copy
`skills/3d-auto-fabrik/SKILL.md` there (rename to
`3d-auto-fabrik.md`); bundle `references/` beside it and mention the
relative paths in the rule, or rely on the global Agent Skills path if your
version supports it.

## Generic / other MCP clients

Any client that speaks stdio MCP can launch the binaries directly:

```json
{ "mcpServers": {
    "cura":      { "command": "/home/YOU/.cargo/bin/mcp-cura" },
    "moonraker": { "command": "/home/YOU/.cargo/bin/mcp-moonraker" }
} }
```

If the client has no skills support, inline `SKILL.md` into its persistent
instructions file (`AGENTS.md`, `GEMINI.md`, or the client's custom-instructions
field) — it is ordinary markdown and works as such, just without
progressive disclosure.

## Client-side tool filtering (read this if a tool "doesn't exist")

Clients filter MCP tools independently of the servers' own policy —
e.g. OpenCode `permissions` deny-rules on `moonraker_*`, Claude's
`allowedTools`/`disallowedTools`, Gemini's `includeTools`/`excludeTools`.
If the agent reports a server-connected-but-tool-missing situation, look at
the client filter first, then the server policy (`moonraker_policy_info` /
`cura_policy_info`), then `print-config`.

## Verifying the whole chain

```sh
sh skills/3d-auto-fabrik/scripts/check-setup.sh
mcp-cura doctor --json
mcp-moonraker doctor --json
```

Then, in the agent: "run mcp-moonraker verify connection and tell me the
Klipper state". A clean answer means the chain works end to end.
