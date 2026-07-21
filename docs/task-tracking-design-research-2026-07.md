# Task-tracking design — research for a queue-tracking hardening spec

Research groundwork for hardening this repo's own `specs/<slug>/tasks/*.md`
task-tracking system: a single-source-of-truth header parser, a persisted
ready-work index, `Depends on:` referential integrity, richer relation types,
collision-resistant task IDs, and a SQLite coordination layer for real
multi-writer concurrency. Gathered via adversarial comparison against Steve
Yegge's `beads` (a graph-based issue tracker built for AI coding agents) plus
general markdown-vs-structured-store critique literature.

Status: research complete (2026-07-16); extended 2026-07-21 with a
transcript survey quantifying the token cost, beads' actual
status/handoff-compactness mechanisms (`bd prime`, `bd show --short`,
`bd ready`), and a design comparison against this repo's own existing
header-parsing machinery (found, on inspection, to already cover more of
beads' ready-work/dependency-resolution surface than first assumed — see
"Design comparison" below). This is the design record; the implementable
work is split into two specs, each citing this doc rather than restating
it: `specs/cheap-task-status-checks/SPEC.md` (status representation) and
`specs/structured-handoff-headers/SPEC.md` (handoff representation).

## Table of contents

Beads (bd) — design and stated rationale · Similar tools and the
markdown-vs-structured-store discourse · Multi-writer concurrency: SQLite vs.
Dolt for this repo's actual need · Design comparison: this repo's approach
vs. beads/Dolt, technique by technique

## Beads (bd) — design and stated rationale

Verified: 2026-07-16

Sources: `github.com/steveyegge/beads` (README/repo), Yegge's Medium posts
("Introducing Beads," "The Beads Revolution").

- **Problem it targets**: coding agents "have no memory between sessions,"
  acting on "whatever video cassette they find in the recorder when they wake
  up" — Yegge found "six hundred and five markdown plan files in varying
  stages of decay" from ad hoc agent task tracking.
- **Data model**: Dolt (version-controlled SQL, cell-level merge, native
  branching), embedded via `bd init`; `.beads/issues.jsonl` is "an export for
  viewers and interchange, not the source of truth." An earlier blog post
  described a simpler "JSONL checked into git" model — the repo's current
  README supersedes that framing with the Dolt-backed one.
- **Dependencies**: `bd dep add <child> <parent>` links tasks via
  blocks/related/parent-child, plus relates-to/duplicates/supersedes/replies-to
  for knowledge-graph-style provenance edges.
- **Ready work**: first-class query, `bd ready` / `bd ready --json` — "a
  definitive list of unblocked work," not something a consumer re-derives.
- **Collision resistance**: hash-based IDs (`bd-a1b2`) "prevent merge
  collisions in multi-agent/multi-branch workflows" by construction.
- **Concurrency**: local Dolt merge, or `dolt sql-server` for real concurrent
  writers with row/cell-level merge — genuine ACID semantics, not
  optimistic-retry.
- **Stated criticism of markdown/ad hoc tracking**: "Markdown plans are text,
  not structured data, and need to be parsed and interpreted... steals GPU
  cycles"; "not queryable... extremely hard to build a work queue from
  markdown plans"; "agents rarely update the plans as they work, so the plans
  bit-rot very fast."
- **Maturity**: v1.1.0 (Jul 2026), ~93 releases, ~25.4k GitHub stars, 312 open
  issues, installable via `brew`/`npm`. No explicit production-readiness
  label found.

## Similar tools and the markdown-vs-structured-store discourse

Verified: 2026-07-16

- **Task Master AI** — PRD-to-dependency-aware-tasks, CLI/MCP/dashboard.
  (`taskmaster.one`)
- **Backlog.md** — explicitly markdown-native (not a DB replacement); three
  human review checkpoints (spec/plan/code); argues markdown is portable,
  git-diffable, human-reviewable, no server dependency.
  (`github.com/MrLesk/Backlog.md`)
- **tasks.md** — "lightweight spec for AI agent task queues," AGENTS.md
  companion. (`tasksmd.github.io`)
- **Linear MCP / Jira MCP** — first-party remote MCP integrations letting
  agents work structured trackers directly; friction noted from Jira's
  complex data model (ADF, custom fields).
- **Scaling-wall critique**: teams hand-roll file locking, custom indexing,
  journaling, ACLs, and metadata schemas on top of markdown — "reinventing a
  database badly" (Volodymyr Pavlyshyn, "The Scaling Wall").
- **Concrete markdown failure mode**: past ~40 sessions, an activity log
  markdown file is too large to read in one pass; agents then read only the
  latest session and lose ~20-sessions-back context.
- **Defenses of plain markdown**: "agents already deeply understand markdown
  from training-data exposure"; a scope argument that markdown fits "Local
  Agents" (finite, structured context) while databases fit "Enterprise
  Agents" (millions of records) — not a universal win either direction.
- **HN reception is split**: one prominent thread stripped Beads down to a
  single-file flat-file tool, keeping only the dependency-graph concept —
  reported as "sharply divided on whether token spend produces commensurate
  value" (search-engine synthesis, not a verified direct quote).

## Multi-writer concurrency: SQLite vs. Dolt for this repo's actual need

Verified: 2026-07-16

This repo's current coordination mechanism is git-native optimistic
concurrency: re-read the task file immediately before flipping `Status`, an
exact-match edit, commit path-scoped, push, then re-confirm at HEAD before
dispatching (`.claude/skills/drain/SKILL.md:162-169`, reference.md:244-250).
This is **correct** — git's push-rejects-on-non-fast-forward is a legitimate
compare-and-swap primitive, and the claim happens before a worker is
dispatched, so a lost race costs a retried git operation, not a wasted
worker.

What it does not give is **throughput under real contention**: every claim
is a full commit + push + possible pull-and-retry round trip to a remote
host, with no stated backoff, and a losing retry re-scans the whole queue
from the SKILL.md-documented inventory step rather than retrying a narrow
operation.

Two distinct flavors of "multi-writer" need different fixes:

| Flavor                                                                                      | What it needs                                        | Fix                                                                                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Many concurrent claimers racing against one always-reachable shared queue                   | Atomic claim-and-mark, no git-push retry storms      | A **local SQLite coordination/index layer** (Python stdlib `sqlite3`) gives real transactions (`BEGIN; claim if unclaimed; COMMIT`) for the actual contention-sensitive operation. No new dependency, no branch-merge machinery needed. |
| Genuinely offline/branch-divergent writers whose queue state forks and must later reconcile | Cell-level merge across diverged copies of the state | This is Dolt's actual differentiator — SQLite has no native answer here.                                                                                                                                                                |

This repo's confirmed need (per the maintainer, 2026-07-16) is the first
flavor only — many agents/orchestrators racing to claim from one live,
reachable queue, not offline branch-divergent state needing merge. A local
SQLite index that is always rebuildable from the markdown task files (git +
markdown stays the durable, human-readable source of truth; SQLite is a
derived, disposable coordination layer, never a second source of truth the
way beads' Dolt store is relative to its git-exported JSONL) is the
architecture decided for the hardening spec. Adopting `bd`/Dolt directly was
explicitly ruled out: it would introduce a new binary dependency across this
repo's three mirrored runtimes (`.claude/` → `antigravity/` → `codex/`,
`.claude/rules/mirror-verification.md`'s manual-pending escape exists
precisely because not every runtime has a scriptable headless story for a
new external tool), and it would introduce a second source of truth (Dolt)
alongside git, the same class of drift risk this hardening effort is meant
to remove, not add.

## Design comparison: this repo's approach vs. beads/Dolt, technique by technique

Verified: 2026-07-21

The actual constraint governing every decision below: **git stays the sole
source of truth, and no external dependency is introduced.** That's the
real bar — not "reject anything beads/Dolt happens to do." Where a beads
technique is achievable without breaking either constraint, this repo
adopts the technique natively; where a technique inherently requires the
thing being ruled out (a second authoritative store, a new binary or
server), it's left out for that stated reason, not a vague "beads has it."

A 2026-07-21 transcript survey (~70 sessions in this repo plus a sibling
repo, `~/hub`, using the same conventions) quantified the actual cost of
today's gaps: **278 unbounded `Read` calls against `specs/*/tasks/*.md` /
`QUEUE.md` / `HANDOFF*.md` / `DRAIN-OWNER.md`, vs. only 136 limited
(`offset`/`limit`) reads** — roughly 2:1 toward pulling an entire 4.7–8.5KB
file to learn a single `Status:` line. One session
(`5fdf5912-784b-4cd5-99c9-2126db0e6cc8`) re-read the same 8,510-byte task
file 7 times; one `/agentic:drain` run
(`2ef60b45-2141-4410-8eb4-a2985babd531`) made 25 full-file task reads
against only 10 `git push` calls. `grep '^Status:'` appears only 32 times
and `head` on a task file only 19 times corpus-wide, vs. 278 unbounded
reads — the cheap path is barely used.

**Where this repo already matches beads' techniques, natively, without
adopting Dolt — confirmed by reading the actual code, not assumed:**

- **Ready-work computation.** Beads' `bd ready` gives "a definitive list of
  unblocked work." This repo's `.claude/skills/drain/drain_frontier.py`
  already does the equivalent: stdlib-only Python, using the shared
  `.claude/skills/_shared/headers.py` regexes, it parses every task's
  `Status`/`Depends on`/`Priority`/`Touch`/`Unblock` fields, resolves
  dependencies, and emits `dispatchable`/`admissible`/`blocked` sets.
  Drain's own `SKILL.md` step 1 already treats its output as authoritative
  for dispatch. This was ALREADY BUILT before this research pass started
  looking for it — a first draft of the implementation spec proposed a new
  `tasks_index.py` to recompute this, which an adversarial review caught
  as duplicating already-authoritative machinery (the exact "second source
  of truth" risk this whole effort exists to avoid, just self-inflicted
  instead of imported from Dolt).
- **Dependency referential integrity.** Beads' Dolt-backed dependency edges
  reject a reference to a nonexistent issue. `drain_frontier.py` already
  detects the equivalent — a diagnostic of kind `unresolved-external-dep`
  — but (confirmed by reading `main()`) never fails the run on it: the
  only nonzero exit is a malformed `Status:` value. The detection logic
  was already correct; only the failure signal was missing. Fixed as a
  single additive `--strict` flag reusing the existing diagnostic list
  verbatim (`specs/cheap-task-status-checks/SPEC.md`), not a new
  implementation.
- **A compact handoff/session-resume artifact, distinct from full task
  content.** Beads' `bd prime` outputs "AI-optimized markdown... ~50
  tokens" in MCP mode specifically so an agent doesn't need to re-read
  everything after context compaction. This repo's `HANDOFF.md` has no
  equivalent today — it's prose-narrative only (8.2–8.5KB observed), and
  when `hooks/handoff-resume` finds multiple candidates, picking the right
  one currently means reading each one's full body. `bd prime`'s technique
  — a compact header ahead of/instead of the full content — is adopted
  natively as a fixed few-line block (`Status`/`Next step`/`Resume with`/
  `Blocking on`) ahead of `HANDOFF.md`'s unchanged prose
  (`specs/structured-handoff-headers/SPEC.md`).

**Where beads/Dolt does something this repo doesn't match, and why that's
an honest trade rather than an oversight:**

- **Collision-resistant hash-based IDs** (`bd-a1b2`) prevent two
  concurrently-created tasks on different branches from silently colliding
  on one identity. This repo's task identity is a numbered filename —
  collision-prone the same way in theory, but in practice two branches
  independently creating a same-numbered task file already produce a
  normal git add/add conflict at merge time, forcing explicit human/agent
  resolution rather than a silent identity merge. Not a perfect
  substitute, but adequate for the observed failure mode; adding a hash-ID
  scheme on top would solve a problem with no evidence it currently causes
  harm here.
- **A local claim/lease mechanism for live multi-agent contention.**
  Beads' unreleased roadmap (per its CHANGELOG, checked 2026-07-21 — no
  release since v1.1.0 2026-07-04) is adding work leases with heartbeat: a
  claimer that dies mid-task gets detected and its claim released. A first
  draft of the implementation spec proposed a local SQLite pre-check for
  the same reason (skip dispatching against a task another worker already
  claimed). Dropped on review: `DRAIN-OWNER.md`'s per-spec git-CAS lease
  already ensures only one drain generation dispatches against a given
  spec's tasks at a time, and a single drain instance's own concurrent
  dispatch (`admission.py`) computes its Touch-disjoint group from one
  sequential frontier computation, not a live race between processes — the
  race this mechanism would solve does not appear to actually occur under
  the current architecture. Revisit only if a genuine concurrent-claim
  race is demonstrated, not merely plausible.
- **Richer relation types** (blocks/relates-to/duplicates/supersedes) and
  an actively maintained, widely-used OSS project (~25.4k stars) providing
  all of this across any repo, not just this one. This repo's `Depends
on:` is the one relation type it hardens; richer types are a plausible
  follow-on, not implemented here — orthogonal to the specific
  status/handoff token-efficiency problem the current spec pass targets.
- **A running Dolt/Postgres-style server for concurrent ACID writers** —
  correctly out of reach regardless of the above: it requires an
  always-on external process, which nothing in this repo's confirmed use
  case (many local claimers, one always-reachable queue, no offline
  branch-divergent writers) needs.
