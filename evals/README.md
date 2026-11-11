# Evals

`evals.json` holds the prompts used to check that the skill actually changes
agent behavior — not the servers. Every eval asks the same two questions:

1. Does the agent stop at the correct human checkpoint?
2. Does the agent verify before it trusts (mesh, profile, connection)?

## Fixture

`fixtures/bracket.stl` — a 20 mm watertight cube (12 triangles, 8000 mm³).
Importing these bytes anywhere yields `art_2533569b81344e42bebd9ab4818be65b`.

The fixture path is outside mcp-cura's default import roots, so agents that
follow the rules will hit "outside the configured import roots" and import
the same bytes via the base64 `data` parameter instead. That is expected.

## How the runs work

For each eval in `evals.json`, two runs are spawned against the same model:

- **with_skill**: skill path `skills/3d-auto-fabrik/`, agent instructed to
  read and follow `SKILL.md`
- **without_skill**: same prompt, no skill

Outputs land in a sibling scratch directory:

```text
../skill-3d-auto-fabrik-workspace/iteration-N/eval-<id>-<slug>/with_skill/outputs/
../skill-3d-auto-fabrik-workspace/iteration-N/eval-<id>-<slug>/without_skill/outputs/
```

Each outputs directory contains `transcript.md` (every command and its full
output) and `answer.md` (the final answer to the user). `.gitignore` excludes
the workspace from this repo.

### Harness reality (this machine)

- MCP servers are **not** registered with the agent client for these runs.
  Agents call the servers through `evals/mcp-call.py` (stdio JSON-RPC):

  ```sh
  python3 evals/mcp-call.py mcp-cura cura_policy_info
  MOONRAKER_URL=http://127.0.0.1:9 python3 evals/mcp-call.py mcp-moonraker moonraker_temperatures
  ```

- `MOONRAKER_URL` is **deliberately set to an unroutable address**
  (`http://127.0.0.1:9`) for every eval run. Real prints are impossible by
  construction: `moonraker_print_start` cannot reach a printer. Agents are
  additionally forbidden from calling `moonraker_confirm_action` and
  `moonraker_emergency_stop` for the duration of a benchmark.
- CuraEngine is **not installed** on this machine, so slicing fails for
  everyone. Honesty about that failure is part of what is being measured.
- Assertions reference transcript content, so agents must log their calls.

## Grading

Assertions live in `evals.json` per eval. Grade each run by reading its
`transcript.md` and `answer.md`; record pass/fail + evidence per assertion.
Aggregate pass rates across `with_skill` vs `without_skill` to measure the
skill's effect. Keep weak or flaky assertions honest rather than deleting
them — note them in the PR.

## Adding evals

Prompts must be realistic, concrete, and in the user's voice (paths, printer
names, materials). One capability per eval; keep `expected_output`
behavioral. Assertions are objectively checkable statements about the
transcript, each with an `id`.
