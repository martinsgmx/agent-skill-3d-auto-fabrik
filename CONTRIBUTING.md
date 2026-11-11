# Contributing to skill-3d-auto-fabrik

Thanks for helping. This repo is small on purpose: one skill, two companion
MCP servers, a lot of care around a heated machine.

## Ground rules

1. **Safety wording is load-bearing.** Never weaken a gate, an approval
   rule, or a "stop and ask" in `SKILL.md` or `references/safety-approvals.md`
   in a "helpful" refactor. If you think a rule is wrong, open an issue
   describing the failure case first.
2. **Tool catalogs are generated.** Edit the servers (they live in their own
   repos) or run `python3 scripts/generate-tool-reference.py` — never
   hand-edit the table rows in `references/mcp-*-tools.md`.
3. **Keep SKILL.md lean.** The body budget is 500 lines. Detail belongs in
   `references/`. Follow progressive disclosure.
4. **Honest docs.** No invented URLs, no unverified commands. If it hasn't
   been run, say so.
5. **No ML-generated slop.** Write like a human engineer. Precise, warm,
   direct.

## Development workflow

```sh
git checkout -b your-change
python3 scripts/validate-skill.py        # must stay green
python3 scripts/generate-tool-reference.py   # after MCP server upgrades
sh skills/3d-auto-fabrik/scripts/check-setup.sh
```

CI runs the validator on every PR. Local MCP servers are required only for
the generator script and the smoke check — not for docs changes.

## Test the skill with your agent

Two complementary checks:

- **Smoke**: paste a prompt from `evals/evals.json` into OpenCode / Claude /
  Gemini CLI with the skill installed; confirm the agent follows the gates.
- **Deep**: run the skill-creator eval loop (spawn with-skill and
  without-skill runs per prompt, grade with `agents/grader.md`). See
  `evals/README.md` for the layout. Do not weaken assertions to make a run
  pass.

## Commit style

Conventional commits, imperative subject:

```text
docs(platforms): fix Windsurf mcp_config path
fix(skill): keep confirm rule out of the monitoring section
feat(references): regenerate tool catalogs for mcp-cura 0.2.0
```

## Pull requests

- One concern per PR.
- Fill the PR template; check the safety box only if you actually checked.
- If behavior changes, say which eval prompts should be re-run.
- Bump `metadata.version` in SKILL.md and add a `CHANGELOG.md` entry when
  the skill's instructions change.

## Reporting bugs and safety faults

- Ordinary bugs: open an issue with the template.
- **Gate bypass / approval flaw / wrong temperature accepted**: security
  vulnerability — see [SECURITY.md](SECURITY.md). Do not open a public
  issue.
