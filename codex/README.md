# Using this toolkit with OpenAI Codex CLI

The toolkit keeps one procedure source in `.claude/skills/`. Codex discovers
those same directories through `.agents/skills/` symlinks, so a skill edit is
available to both runtimes without a copied port. The repository gate checks
that every source skill has a valid Codex entrypoint.

## What Codex consumes

Codex reads the shared skills and the same data layer as Claude Code:

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

A Codex session run from this checkout can invoke the repository skills
directly. Skills select a runtime capability where orchestration differs:
Claude Code uses Workflow, while Codex uses awaited collaboration subagents.
Both paths use bd for claim and closure state.

## Why the skills are linked

Copied runtime trees drift. Symlinks preserve one procedure source while
letting each runtime use its native discovery path. Runtime-specific behavior
belongs in capability-based branches inside that shared procedure.
