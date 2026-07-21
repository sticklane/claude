# Evidence base for the agentic core redesign

Findings from the 2026-07-21 full-system audit (five repo/web research
passes), the ctx utilization review, and the beads verification work.
Pointers are to files in this repo or primary external sources.

## Flow-control placement (prose vs code)

- Tested code owns the read side: `drain_frontier.py` (408 lines, 377
  test lines), `admission.py` (400 lines, 752 test lines incl. a real
  multi-process race), `screen-stub.sh`, `_shared/*.py`.
- Prose owns the loop: drain SKILL.md (504 lines) + reference.md
  (2,033) encode dispatch iteration, verdict routing (SKILL.md
  §3), baton arithmetic (§3a: `max(2,6−W)`), CAS status flips, and
  diff-base recovery via commit-message grep (reference.md:940-966).
  None of it is unit-tested; coverage is model-run evals plus a
  phrase-grep manifest that by its own text cannot catch reordering or
  mirror-added content (.claude/rules/mirror-procedure-discipline.md).
- Failure signature: specs/drain-wake-cost EVIDENCE — the baton
  trigger did not fire because the model never emitted it; the fix was
  prose, "model-remembered, not enforced."

## State schema

- No schema file or validator exists (`**/*.schema.json` → zero hits).
- Grammar = 4 regex parsers (`_shared/headers.py`, `list_specs.py`,
  `prioritize_scan.py`, `status.sh`); `Budget:`/`Rigor:` have no
  shared regex. Header-field list restated ~6× across three runtime
  trees; verdict contract ≥4×.
- Worker verdicts: ≤2k-token semi-structured prose re-parsed by the
  hub model per collection (drain reference.md:859-879), while the
  Agent tool natively supports schema-forced structured output.

## Handoff redundancy

- One gen-5 drain run simultaneously carried: task Status headers
  (canonical per SKILL.md:16-22), DRAIN-BATON.md, DRAIN-OWNER.md,
  .claude/HANDOFF-drain-hub.md, HUMAN.md entries.
- Contradiction: resume-handoff SKILL.md:31 forbids re-deriving
  captured state; drain's fresh-instance ritual R1a (SKILL.md:322-327)
  mandates reconciling and drift-checking it.

## Gate placement

- 24 draft stubs across 9 finished specs parked on manual promotion —
  the largest single queue blocker — while the stub path already has a
  deterministic screen + re-authoring + critic gate.
- /prioritize carries a launch contract though it only rewrites
  Priority headers in one revertible commit (thin per
  docs/human-gates.md's own five-reason test).
- quality-discipline.md opens "any code change, attended or
  unattended" then scopes doc-currency to attended only (:70-84).

## ctx utilization (the adoption case study)

- specs/ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md
  (~1,100 transcripts): ~1 organic use in ~14 post-rollout sessions;
  zero subagent invocations ever; 0% compliance with 6 "prefer ctx"
  worker prompts (workers ran 99–124 greps); ~300 greps mapping 1:1 to
  ctx commands; notes feature never used; skill auto-triggered 0
  times.
- Structural causes: no `Bash(ctx *)` grant anywhere (scout.md:4,
  critic.md:4, no settings permissions block); token-discipline.md
  routes structure questions to scout, which cannot run ctx;
  worktrees index-cold (cache gitignored).
- Positive controls: budget_analysis 35b223ab (3 task files from 2
  `ctx tree` calls, zero source reads); fooszone cfd7ce8f (3-way dup
  found via `ctx refs`).
- Trust burns: figureBboxes absence fallacy (specs/ctx-absence-check),
  minified `map` ~90% noise (specs/ctx-minified-skip), silent empties
  (specs/ctx-output-shape-gaps).

## External design points (primary sources)

- Aider repo map: injected every request under a token budget — the
  push model with no adoption problem by construction
  (aider.chat/2023/10/22/repomap.html).
- Cursor semantic search: +12.5% answer accuracy vs grep-only, hybrid
  beats either alone (cursor.com/blog/semsearch).
- Anthropic multi-agent research system: multi-agent ≈ 15× chat
  tokens; effort-scaling heuristics
  (anthropic.com/engineering/built-multi-agent-research-system).
- beads (github.com/steveyegge/beads): `bd ready` dependency-aware
  frontier; `discovered-from` as first-class edge
  (docs/core-concepts/dependencies.md); native acceptance-criteria
  field (docs/reference/json-schema.md); CLI-over-MCP for token cost
  (~2k vs tens of thousands, FAQ); storage evolved JSONL+SQLite →
  Dolt, `.beads/issues.jsonl` demoted to passive export, sync via
  custom ref `refs/dolt/data` (discussion #2332); embedded
  single-writer flock vs `dolt sql-server` modes; semver 1.x, storage
  changed twice in ~5 months (DoltHub blog 2026-04-02).
- Temporal/LangGraph: deterministic code owns control flow and
  retries; typed checkpoints enable resume (docs.temporal.io,
  docs.langchain.com/oss/python/langgraph/persistence).
- Backlog.md: the CLI is the write path so field types stay consistent
  (github.com/MrLesk/Backlog.md) — adopted as the wrapper's
  sole-writer principle.

## Cost telemetry already in-repo

- specs/drain-wake-cost/EVIDENCE.md: ~$1,406/week unstructured
  orchestration; general-purpose at session-frontier model cost MORE
  per call than the opus-pinned worker ($0.067 vs $0.057, 2026-07
  agentprof week).
- token-discipline.md: the 2026-07-11 $123 nested untyped-agent chain.
- Both occurred with the relevant rules text in place — doctrine
  without mechanism.

## Critique pass (critic agent, 2026-07-21)

Verdict NOT-READY on the first draft; all findings folded into the
spec in the same session. Blockers: (1) no `## Acceptance criteria`
mapping the R-\* requirements to runnable checks — section added, one
anchored check per requirement; (2) the budget cap rested on an
unspecified cost signal absent on generic runtimes — layered spend
signal specified (harness telemetry else wrapper estimate) as new
requirement R-M. Majors: tracker-store/worktree topology undefined
(resolved: single-writer, primary-checkout-only, workers never write);
runtime-adapter conversion had no migration step (added as step 5 with
interim mirror-manifest retirement); step 2 flipped source of truth
before readers were re-pointed (resolved: shadow mode until step 4
cutover); R-B bootstrap over-claimed a co-located-Dolt-remote result
(resolved: committed-JSONL import is the canonical recipe, Dolt
remotes optional). Minors: latency scale check added to acceptance;
grant enforceability on grant-less runtimes stated honestly
(UNENFORCED marker + composer-boundary floor); Next stage line given
its artifact path.

## Second critique pass + boil-down (2026-07-21)

A second critic run against the rewritten spec returned NOT-READY
with two majors, both about write discipline: (1) "one tracker
writer" was a convention, not a mechanism, and the R-C acceptance
test raced a topology the design forbids instead of the race the
sync design introduces; (2) cross-clone consistency was unspecified
while the repo demonstrably runs concurrent sessions in separate
clones. Resolved by making both mechanical: D8 (repo-level write
lock on all tracker-write commands) and D9 (pull → import → apply →
export → commit → push, re-apply on push rejection, JSONL never
hand-merged), with R-C's acceptance replaced by a same-machine
lock test and a two-clone race test. Minors resolved: restored the
named reader list in migration step 4, both mirror rules files and
CLAUDE.md's port-chain conventions in step 5, the F12
worktree-resolution fact behind "workers never write", per-iteration
export batching, and cut the unconsumed memory-compaction purchase
justification.

A maintainer-directed boil-down (reduce the document to plain
statements; gaps mark unclear ideas) exposed and fixed additional
mush the structural passes missed: "judgment framing" became "the
repo's worker instructions"; the timer-based "veto window" (nothing
would run the timer) became immediate promotion + inbox listing +
`agentic demote`; the inbox was pinned as a command over tracker
state, not an app; AI-writing vocabulary ("substrate") removed.

## Hands-on bd battery (v1.1.0, this container, 2026-07-21)

Full results in SPEC.md "Substrate verification". Headlines: metadata
JSON field beats labels for structured fields (typed, queryable,
lossless; labels silently truncate at 255 chars and comma-split);
`discovered-from` non-blocking and `parent-child` transitively
blocking as required; `bd ready --claim` is the documented atomic
claim; latency ~0.3s read / ~0.5s write warm, `bd init` 3.5s;
JSONL export→import round-trip lossless with IDs preserved; tracker
state does not ride normal git push/clone — `bd dolt push` publishes,
`bd bootstrap` (~1s) hydrates a fresh clone; `bd init` auto-commits
AGENTS.md/CLAUDE.md/settings edits into the host repo and
`.beads/interactions.jsonl` is tracked telemetry churn — both owned
by the wrapper at adoption. Multi-writer racing deliberately untested
(design requirement R-C, maintainer decision).
