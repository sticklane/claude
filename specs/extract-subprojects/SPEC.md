Status: waiting
Unblock: ask: owner schedules the extraction (needs new sibling repos + release wiring the toolkit repo can't create headless)

# Extract agentprof and agent-console to sibling repos

## Problem

Three substantial subprojects live vendored in the toolkit repo:
`agentprof/` (Go, ~16.7k LOC), `agent-console/` (Python, ~8.6k LOC), and
`context-tree/` (Rust, the `ctx` index). The holistic critique
(agentic-nvl, 2026-07-23) flagged ~25k LOC + two extra toolchains riding in
every clone, with `agentprof`/`agent-console` checks wired into neither the
canonical `scripts/check.sh` nor CI. Only `context-tree` is genuine core
(the `ctx` skill and 6+ others depend on it) — and even it is consumed as a
binary, not as source.

Owner decision (2026-07-23, agentic-2my): **extract `agentprof` and
`agent-console` to sibling repos consumed as installed binaries; keep
`context-tree` but ship `ctx` as a released binary rather than vendored Rust
source.** This spec is the plan; execution is owner-scheduled (it needs new
repos, CI, and release wiring that cannot be created from inside this repo
headless).

## Requirements

- R1 — `agentprof/` moves to its own repo. Its history is preserved (git
  filter-repo / subtree split, not a flat copy). The toolkit consumes it as
  an installed binary on PATH; no Go toolchain required to clone the toolkit.
- R2 — `agent-console/` moves to its own repo, same terms (no Python
  dashboard deps in a toolkit clone). Note the `/workboard` live-server hang
  (agentic-wns) travels with it — file it against the new repo.
- R3 — `context-tree/` stays, but `ctx` ships as a released binary the
  installer fetches; the Rust source is not required to use the toolkit.
  (Lighter than a full extraction — a build/release step, not a repo move.)
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
