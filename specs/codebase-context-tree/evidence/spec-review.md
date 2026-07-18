# Spec-completion review: codebase-context-tree

spec review: 0 findings, 0 fixed, 1 discovered

Ref range reviewed: `git diff 99c3d3d7..HEAD -- context-tree/` (the full
cumulative product diff across all 14 tasks — 12 language extractors, the
sync/index engine, query commands, notes CRUD + re-anchoring, LSP
enrichment, the MCP server, git hooks, and integration/e2e tests).

Five parallel scout sweeps (one per major subsystem: language extractors,
sync/index, notes/reanchor, MCP server, hooks + query commands) found no
high-confidence correctness/behavior bugs. One item was raised and
deliberately not fixed — see Discovered below.

`bash context-tree/scripts/check.sh` was green before this review and
remains untouched (no code changes made).

## Discovered

- File-size cast overflow (`context-tree/src/index/mod.rs:291`,
  `context-tree/src/sync/mod.rs:312`) — a u64→i64→u64 round-trip for file
  sizes overflows above `i64::MAX` (~9.2 exabytes), which would corrupt
  size-based staleness detection. Practically unreachable (no real file
  approaches exabyte scale), so left unfixed. Materialized as a draft stub
  for a human to judge whether it's worth a defensive fix.
