# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository scaffold: installable `3d-auto-fabrik` skill,
  platform registration docs and examples, safety and configuration docs,
  CI skill validation, eval prompts, eval fixture (`evals/fixtures/bracket.stl`)
  and a stdio driver (`evals/mcp-call.py`) for running the evals.

### Changed
- Skill: `SKILL.md` / `references/pipeline.md` now state explicitly that the
  base64 `data` parameter of `cura_artifact_import` is the sanctioned channel
  for client-supplied bytes outside the import roots, not a policy bypass.
  (Found by eval-1 with-skill run over-refusing the import.)
