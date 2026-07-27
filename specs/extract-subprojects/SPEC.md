Status: waiting
Unblock: ask: owner schedules the extraction (needs new sibling repos + release wiring the toolkit repo can't create headless)

# Extract agentprof and agent-console to sibling repos

## Problem

Two substantial subprojects live vendored in the toolkit repo:
`agentprof/` (Go, ~16.7k LOC) and `agent-console/` (Python, ~8.6k LOC).
The holistic critique (agentic-nvl, 2026-07-23) flagged their LOC and extra
toolchain/dependency weight, with their checks wired into neither the
canonical `scripts/check.sh` nor CI.

Owner decision (2026-07-23, agentic-2my): **extract `agentprof` and
`agent-console` to sibling repos consumed as installed binaries.**
Code exploration is now supplied separately by the pinned Codebase-Memory
release and is not part of this extraction. This spec is the plan; execution
is owner-scheduled (it needs new
repos, CI, and release wiring that cannot be created from inside this repo
headless).

## Requirements

- R1 — `agentprof/` moves to its own repo. Its history is preserved (git
  filter-repo / subtree split, not a flat copy). The toolkit consumes it as
  an installed binary on PATH; no Go toolchain required to clone the toolkit.
- R2 — `agent-console/` moves to its own repo, same terms (no Python
  dashboard deps in a toolkit clone). Note the `/workboard` live-server hang
  (agentic-wns) travels with it — file it against the new repo.
- R3 — Codebase-Memory remains an external checksum-pinned binary; this spec
  does not fork, move, or package its source.
- R4 — every in-tree reference to the moved trees is rewritten:
  `scripts/check.sh` (drop the subproject sub-checks), `AGENTS.md`'s repo
  map, `docs/` mentions, and any skill that shells into them. A clone with
  the binaries absent degrades gracefully (the depending skill says the
  binary is missing, not a stack trace).
- R5 — the toolkit's own `scripts/check.sh` stays green with the trees
  gone; the moved repos carry their own CI.

## Open questions

- Binary distribution channel (GitHub releases, a tap, `go install` /
  `pipx`)? Sets how R1–R3's installer step is written.
- Does any current skill invoke `agentprof`/`agent-console` at runtime, or
  are they human-run tools? (If human-run, R4 is doc-only.)

## Acceptance

- [ ] Each moved repo builds and its own `scripts/check.sh` is green.
- [ ] `bash scripts/check.sh` in the toolkit is green with `agentprof/` and
      `agent-console/` absent.
- [ ] `grep -rl 'agentprof/\|agent-console/' .claude/ AGENTS.md scripts/` →
      only references that survive as "installed binary" pointers, none that
      assume in-tree source.
