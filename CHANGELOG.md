# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.5] - 2026-11-24

### Added
- URL/ZIP input path: download over http(s) into a unique per-job workspace,
  extract with zip-slip/symlink and size/file caps, and keep the workspace
  until the user confirms cleanup (including after cancel or abort).
- Model discovery in `model_downloaded/files/` (configurable), with
  `.stl`/`.3mf`/`.obj`/`.amf` recognition, `.3mf` as one artifact, listing and
  explicit user choice. `references/job-workspace.md` documents the rules.
- Ready-made G-code branch: validate against live printer facts, mapped
  material limits and policy caps, report PASS/FAIL, then stop.
- Optional Moonraker job-queue stage alongside direct print start.
- `references/printer-materials.md`: live MCP facts as the source of truth,
  user labels mapped to exact preset ids, optional onboarding, and clearly
  illustrative material temperatures.
- A single preflight gate repeated before every mutating stage.
- Evals 5 and 6: URL/ZIP discovery and ready-made G-code validation.
- Cura-name ambiguity decision rule and dialogue: when no mcp-cura tools are
  present, report that, search the active slicer by preset name and require
  explicit confirmation before substituting an Orca preset.
- Three fill-in templates in SKILL.md: Plan confirmation, Stage 5 review and
  Print start.
- Stage 6 transfer decision table, including an explicitly requested same-host
  copy verified with SHA-256, `moonraker_files_list` and
  `moonraker_file_metadata`.
- Artifact-metadata check after import, G-code inspect vs header/summary vs
  Moonraker cross-check, and a scoped Code Mode large-import pattern.
- Evals 7 and 8: Cura-name ambiguity and G-code inspect discrepancy reporting.

### Changed
- Printer and material choices now come from live MCP configuration plus an
  optional user config (`~/.config/3d-auto-fabrik/config.yaml` with a
  project-local override); no fuzzy matching and no config edits by the agent.
- SKILL.md, `references/pipeline.md`, `docs/configuration.md` and README
  describe the new workspace, discovery, preflight and queue stages. The
  skill remains platform-agnostic: only install paths and MCP registration
  differ between OpenCode, Claude and generic clients.
- `*_profile_list` is documented as a bounded index, not proof of absence;
  profile discovery falls back to exact paths via `*_profile_get` and
  `*_profile_resolve` before concluding a preset is missing.
- Troubleshooting covers `kind:other` imports, profile-list misses and
  inspect/summary discrepancies; stage reports now carry the `art_*`, `job_*`
  and `apr_*` ids and exact filenames. Skill version bumped to 0.2.5.

## [0.2.0] - 2026-11-19

### Added
- **mcp-orca support** as the preferred slicing engine, alongside
  mcp-moonraker. The skill now chooses an engine once per job and falls back
  to mcp-cura when Orca is missing, not running, or has no engine configured.
- `references/engine-selection.md` — Orca vs Cura capability matrix, fallback
  rules, profile-model differences, and the artifact-id boundary.
- `references/mcp-orca-tools.md` — generated catalog for the 27 mcp-orca
  tools.
- `mcp-orca tools --json` (upstream companion change) so the catalog
  generator can read risk, gate and arguments without parsing prose.
- Eval 4: Orca engine unavailable — fall back or stop honestly.

### Changed
- `SKILL.md` is now engine-agnostic: shared stages, Orca/Cura tool columns,
  and two approval protocols (Orca decide-then-retry; Cura/Moonraker
  prepare-then-confirm). Version bumped to `0.2.0`.
- `references/pipeline.md`, `references/safety-approvals.md` and
  `references/troubleshooting.md` cover both slicers, including Orca's lack
  of profile verify and G-code verify/prepare.
- `scripts/check-setup.sh` checks all three binaries, requires at least one
  slicer, and reports tool counts.
- `scripts/generate-tool-reference.py` generates all three catalogs and skips
  missing binaries instead of failing the whole run.
- Docs, examples and evals updated for the three-server layout; the skill
  remains MIT while mcp-orca is Apache-2.0.

## [0.1.0] - 2026-11-01

### Added
- Initial repository scaffold: installable `3d-auto-fabrik` skill,
  platform registration docs and examples, safety and configuration docs,
  CI skill validation, eval prompts, eval fixture (`evals/fixtures/bracket.stl`)
  and a stdio driver (`evals/mcp-call.py`) for running the evals.

### Changed
- Skill: `SKILL.md` / `references/pipeline.md` state explicitly that the
  base64 `data` parameter of `cura_artifact_import` is the sanctioned channel
  for client-supplied bytes outside the import roots, not a policy bypass.
  (Found by eval-1 with-skill run over-refusing the import.)
