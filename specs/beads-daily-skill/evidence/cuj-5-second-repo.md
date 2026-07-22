# CUJ-5 — Second repo

Status: MANUAL-PENDING.

The journey requires repeating CUJ-1 and CUJ-2 on a real consuming
repo (the spec names ynab-mcp-server as the example), following only
the written install steps — a test of the plan, not of the author.
This container has no consuming repo checked out, and cloning one
mid-change would test a hand-built environment rather than the
documented path.

What the written path now is (verified in this repo, commit
`2376d48`):

1. Once per machine: the `agentic@agentic-toolkit` plugin + `bd`
   pinned 1.1.0.
2. Per repo: `bd init` (curated), `/gate` — whose installer now
   detects `.beads/` and wires the bd-compliance Stop hook
   automatically, and detects bd-owned `core.hooksPath` so it never
   displaces bd's own git hooks — `Bash(bd *)` allowlist, seed the
   queue.

Run this on the consuming repo and record the transcript here; the
scratch-repo run in cuj-1/cuj-2 is the nearest clean-room proxy until
then.
