# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.

## [Unreleased]

## [0.1.2] 2026-08-01

### Fixed

- **Console output no longer crashes on a legacy codepage.** A Windows console at codepage 1252
  hands Python an `errors="strict"` stream, so writing a non-ASCII character such as the check
  marks this tool prints for each rename step raised `UnicodeEncodeError: 'charmap' codec can't
  encode character` and the command exited non-zero *after* the rename had already been applied.
  Click does not protect against this, and Rich raises the same way through its own writer. The
  new `safe_console` module degrades at the sink: a UTF-8 terminal still receives the character,
  and only a stream that cannot encode it sees `[OK]` / `[X]` / `[!]`. The module-level `Console`
  now renders through `safe_console.safe_stream()`, which resolves `sys.stdout` at write time so
  test harnesses can still capture the output.
- **`make test` can pass at all.** The gate runs `lint-imports` unconditionally, but this project
  had no `[tool.importlinter]` section, so the stage aborted with "Could not read any
  configuration" and failed the whole gate on every run. Added the contract the layout already
  obeys: `cli` sits above `renamer`, `safe_console` and `typed_click`, none of which import
  anything internal, so the core cannot import the CLI.

## [0.1.1]

Added the `typed_click` facade so the rich-click decorators type-check under pyright strict.

## [0.1.0]

Initial release. Renames a project scaffolded from a bitranox template: derives the new name
from the target directory, rewrites every non-binary file, and moves the paths that carry the
old name.
