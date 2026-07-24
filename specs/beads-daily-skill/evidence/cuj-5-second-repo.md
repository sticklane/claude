# CUJ-5 — Second repo

Status: DONE (2026-07-23, bd issue agentic-m22).

The journey required repeating CUJ-1 and CUJ-2 on a real consuming
repo (the spec names ynab-mcp-server as the example), following only
the written install steps — a test of the plan, not of the author.
The cross-repo-beads-adoption workflow performed that live install on
ynab-mcp-server: 13 issues created from the repo's existing task
state, verified non-lossy against the source, and pushed. agentic-m22
was closed done on 2026-07-23 on that evidence.

What the written path now is (verified in this repo, commit
`2376d48`):

1. Once per machine: the `agentic@agentic-toolkit` plugin + `bd`
   pinned 1.1.0.
2. Per repo: `bd init` (curated), `/gate` — whose installer now
   detects `.beads/` and wires the bd-compliance Stop hook
   automatically, and detects bd-owned `core.hooksPath` so it never
   displaces bd's own git hooks — `Bash(bd *)` allowlist, seed the
   queue.

That path is what the ynab-mcp-server install exercised; the
scratch-repo run in cuj-1/cuj-2 remains the clean-room proxy for the
steps it did not re-derive.
