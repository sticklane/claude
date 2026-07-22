# Using this toolkit with OpenAI Codex CLI

This directory no longer holds a ported copy of the pipeline. On
2026-07-22 the toolkit pivoted from procedure-level portability to
**data-level portability** (maintainer-ratified addendum in
[`specs/agentic-core-redesign/SPEC.md`](../specs/agentic-core-redesign/SPEC.md)):
Claude Code is the primary runtime, and the mirrored `antigravity/` and
`codex/` skill trees — plus the mirror manifest, parity gates, and both
mirror rules — were deleted. The old Codex overlay (symlinked skills plus
the `drain`/`build`/`evals` wrappers and `verify-live.sh`) is gone; there
is no longer a per-runtime procedure tree to install or keep in sync.

## What Codex consumes instead

Codex CLI, like any agent runtime with shell access, reads the toolkit's
**data layer** directly — no port of the skills is required:

- **The work queue** — bd (beads): `bd ready --json`, `bd show <id>`, or
  the committed `.beads/issues.jsonl` export. This is the source of ready
  work and its dependency graph.
- **Code structure** — the `ctx` index under `.context/`: `ctx tree`,
  `ctx sig`, `ctx refs`, `ctx deps`, `ctx map`, `ctx at`. Structural
  questions are answered from the index rather than by reading whole
  files.
- **Specs and tasks** — the markdown under `specs/`: each `SPEC.md` and
  its `tasks/*.md`, with the single-line `Status:` / `Depends on:` /
  `Touch:` headers a runtime can parse directly.

A Codex session run from a checkout of this repo works the same queue
Claude Code does by reading those three surfaces
(`codex exec "list the specs in this project and their status"` and the
like). The pipeline discipline itself — tiering, gates, and the
human-launch authorization on the execution stages — lives in
[`.claude/`](../.claude/) and the repo's rules; it is documentation a
capable agent can follow, not a runtime-specific install.

## Why the port was retired

Maintaining three near-identical procedure trees (`.claude/` →
`antigravity/` → `codex/`) cost more than it returned: the prose was
never byte-identical, the parity gates only proved structural
conformance rather than that a mirror still worked, and every skill edit
had to be re-derived by hand into two more places. Data-level portability
gives other runtimes the one thing they actually need — the state — while
letting the procedures evolve in a single home.
