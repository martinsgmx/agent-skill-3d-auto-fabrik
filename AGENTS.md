# AGENTS.md — instructions for AI agents contributing to this repo

You are working on a skill that supervises a **heated machine**.

## Non-negotiables

- Never weaken, reorder or remove a safety gate in `skills/3d-auto-fabrik/`
  (SKILL.md, references/safety-approvals.md) without an explicit human
  maintainer decision in the PR discussion.
- Never hand-edit the generated tables in `references/mcp-cura-tools.md` or
  `references/mcp-moonraker-tools.md`; run `python3 scripts/generate-tool-reference.py`.
- Never invent tool names, arguments, URLs, or platform paths. Verify
  against the binaries (`mcp-cura tools`, `mcp-moonraker tools --json`) or
  the linked docs.
- Keep SKILL.md under 500 lines; put detail in references/.

## Before you finish

```sh
python3 scripts/validate-skill.py
```

If you changed the skill's behavior, add or update a prompt in
`evals/evals.json` and say so in the PR. If you changed a doc that mentions
`cargo install`, keep the sibling-repo layout (`/repos/skill-3d-auto-fabrik`,
`/repos/mcp-cura`, `/repos/mcp-moonraker`) — that is the supported
install path.

## Style

- Plain, precise markdown. Short sentences. No hype.
- Match the existing voice: helpful-senior-engineer, not vendor marketing.
- YAML frontmatter in SKILL.md: only spec fields (`name`, `description`,
  `license`, `compatibility`, `metadata`).
