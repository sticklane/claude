# HANDOFF: research pass BEFORE resuming the drain queue

## Task

**Do this first, before touching the drain queue at all:** a research +
design pass on whether `ctx`'s command surface and CUJ/Reading-ladder
doctrine actually reflect current best practice for how LLM agents should
navigate code — specifically, when an agent legitimately still needs raw
`grep`/`sed`/`awk` versus when it should be using `ctx`'s structured
queries (`refs`/`sig`/`show`/`map`/`deps`/`notes`) instead. This came from
a live question this session: none of the critique/breakdown work done on
the `ctx-*` specs commissioned or checked against research on LLM
tool-use patterns for source-reading — the grounding `docs/guides/ctx-cujs.md`
cites (Aider's token-budgeted repo map, Codebase-Memory arXiv 2603.27277,
Serena/LSP) was inherited from earlier spec-authoring, not verified or
extended this session.

**How to run it:** a `/factcheck` pass (if the question is closing a
known-source factual gap against specific docs/papers) or `/idea` (if it
should produce a new spec directly) — human judgment call, not pinned
here. Feed findings into a new spec under `specs/` (not a modification of
the existing `ctx-*` specs — those are already broken down and
mid-drain, see below).

**Only after that research/spec work is done**, resume the drain queue:
`/drain` (no argument — the whole-queue swarm launch). State is fully
captured in `specs/ctx-cujs/DRAIN-BATON.md` (Run-token
`a750d87976c02e32`, Generation 7) — 3 leases held
(`ctx-absence-check`, `ctx-cujs`, `drain-plugin-path-resolution`), each
with 1-3 more tasks immediately dispatchable, plus 5 more
`Breakdown-ready: true` specs untouched this run
(`ctx-skill-token-doctrine` highest-leverage — see the baton's "Next
actions" list for the full picture). Do not re-derive this from
conversation memory; the baton file is authoritative.

## State

- Done, verified, pushed to `origin/main`: everything described in the
  baton above (agentprof-skill-audit spec fully closed this run; 3 ctx
  specs broken down and their first tasks landed).
- Nothing uncommitted, nothing in flight — the orchestrator worktree
  `.claude/worktrees/drain-orchestrator` and all per-task worker
  worktrees were cleaned up as each task merged.
- No collision risk, no HUMAN.md items filed this session beyond the
  pre-existing ones (unrelated, from earlier work).

## Verification

Not applicable — this handoff's own content is a routing instruction
(do X before Y), not a claim about code correctness. The underlying
drain work's verification evidence lives in each merged task's own
`## Acceptance` checkboxes and the spec `evidence/` files, per commit.
