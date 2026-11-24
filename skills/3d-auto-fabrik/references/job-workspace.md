# Job workspace, downloads and model discovery

Expanded companion to SKILL.md's "Job workspace and input discovery". Load
this at the start of any job whose input is a URL, an archive, a loose folder
of models, or an unclear file. It exists to stop one job's files leaking into
another and to keep archive handling boring.

## One workspace per job

Create a fresh directory before touching the input:

```text
${TMPDIR:-/tmp}/3d-auto-fabrik/job_<UTC-timestamp>_<random-hex>/
```

- Use the platform-neutral temp root. Do **not** hard-code a client-specific
  path such as a single editor's temp directory — this skill must behave the
  same on OpenCode, Claude and generic clients.
- The name is unique. Never reuse a name, never write into another job's
  directory, and never keep a shared "current model" scratch file. Record the
  full path in the job notes and check it before each write.
- Everything for this job lives here: the downloaded archive, extracted
  files, any notes, and any temporary reports. Artifact ids stay in the
  slicing server's workspace, not here.
- Keep the workspace until the job is over. Offer to delete it after a
  completed print, and also after cancel or abort. Delete only after explicit
  confirmation; "no" means keep it.

## Input 1 — a URL to a ZIP

1. Accept `http` and `https` only. Reject other schemes, embedded credentials
   and local file URLs. Re-check the scheme after every redirect.
2. Cap the download at 512 MiB (matching mcp-orca's `max_import_bytes`).
   Report an oversized or failed download in the tool's own words — never
   fabricate a file.
3. Confirm the bytes are a ZIP before extracting. Save the original archive
   in the job workspace under its original name.
4. Extract **into the job workspace**, under a directory named after the
   archive, so two archives cannot overwrite each other.

### Archive safety

- Reject entries with absolute paths, drive prefixes or any `..` component
  (zip-slip). Reject symlinks and hardlinks.
- Cap total extracted size (~2 GiB) and file count (~1000). On breach, stop
  and report; do not extract a truncated archive.
- Do **not** recursively unpack nested archives. List them as assets and ask
  the user whether to open one, into another uniquely named directory.
- Never run files from the archive. Models and G-code are data, not scripts.

## Input 2 — a loose folder of models

The default model drop directory is `model_downloaded/files/`, relative to the
workspace root and configurable as `drop_dir` in the user config. It is often
only loosely organised; that is expected. The goal is to find printable
assets, not to judge the folder layout.

- **Do not create the directory.** If it is missing, say so and ask for a
  path or a URL.
- Scan recursively. Skip hidden directories (`.git`, `.DS_Store`, …) and
  `__MACOSX`. Ignore junk files rather than listing them.
- Scan the extracted archive directory first, then the drop directory. Show
  which source each candidate came from.

## What counts as a model

| Extension | Treatment |
| --- | --- |
| `.stl`, `.obj`, `.amf` | model candidate |
| `.3mf` | **one** model candidate — it is already a ZIP; never unzip it ourselves |
| `.gcode` | route to the ready-made G-code validation branch in SKILL.md |
| everything else | asset: list it, do not import it |

## List, then ask

Always show the user what was found before importing: relative path, format
and size from inside the job workspace. If there are many candidates, show the
first ~20 and add "and N more" rather than flooding the transcript.

Then ask which file(s) to use. Never pick by filename, order or modification
time. When several models are selected, ask whether they are separate objects
on one bed or one merged artifact: `orca_mesh_merge` / `cura_mesh_merge` is a
triangle **soup**, not a boolean union, and must never be applied silently.

## Importing the chosen files

- Discovered bytes go through the base64 `data` channel of
  `orca_artifact_import` / `cura_artifact_import`, with `name`, `kind` and
  `format` set. This needs no policy change.
- A path under an import root may be used when the user named that path
  directly. Never widen `import_roots` just to make one job pass; if a path is
  refused, re-import the same bytes via `data` (content-addressing returns the
  same artifact id).
- Record each returned `artifact_id`. Artifact ids belong to one server only —
  never pass an Orca id to Cura or the reverse.

## Importing large artifacts from a Code Mode runtime

The `data` channel is still the sanctioned path. A Code Mode `execute` runtime
may expose no filesystem import (`node:fs` unavailable) and may block
`fetch('file://…')`, so a multi-megabyte STL cannot be read straight into the
call. Keep the workaround boring and scoped:

1. Check for a runtime-provided file/artifact helper first and use it if one
   exists. Do not assume the workaround is needed.
2. If none exists, stage the base64 under the client's approved scratch area
   (for OpenCode, `/tmp/opencode`), serve it from a localhost-only HTTP server
   bound to `127.0.0.1`, fetch it over `http://127.0.0.1:<port>/…` in
   `execute`, and import through `data` with explicit `name`, `kind`, `format`.
3. Kill the server and delete the staged file in the same turn, including on
   failure. Never leave a listener or scratch bytes behind.
4. Do not widen `import_roots`, do not stage on a public/external URL, and do
   not alter geometry to force an import. If the import returns an unexpected
   kind, follow the artifact-metadata check in SKILL.md Stage 1 instead of
   retrying blindly.

## Cleanup checklist

- [ ] Temporary transfer files and localhost helper servers: removed immediately after use.
- [ ] Per-job workspace: kept until the user confirms deletion; offered again on cancel or abort.
- [ ] Final summary: exact created G-code filename(s), destination path and the `art_*` / `job_*` / `apr_*` ids touched.
