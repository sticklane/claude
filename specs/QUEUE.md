# Combined queue — wave plan (canonical, single copy)

**Queue 6 (drained 2026-07-12)** — the three overnight-review specs:
agentprof-scrub-hex-tokens (shx), session-refresh-automation (sra),
untyped-agent-fanout (uaf). 11 tasks, one repo-wide drain. Contention
points and their machine-expressed resolution: token-discipline.md
(uaf 03 carries a cross-spec `Depends on:` path to sra 01),
costsummary + agent-console (uaf 04 → sra 02 and sra 05). Groups are
per-spec as always: sra 01+02, sra 04+05, uaf 03+04. plugin.json bumps
never co-run (sra 04 is the only bump in its group; uaf 03 in its; uaf
02's is conditional and solo-ordered behind uaf 01).

| Wave | Tasks (parallel within a wave) |
|---|---|
| 1 | shx 01; uaf 01 runs solo whenever admitted (read-only trace) |
| 2 | shx 02 |
| 3 | sra 01; sra 02 |
| 4 | sra 04; sra 05 |
| 5 | sra 03 |
| 6 | uaf 02 |
| 7 | uaf 03; uaf 04 |

All 11 tasks `Status: done`, one repo-wide sequential drain (W=1), each
merged + pushed individually with gates green (`specs/status.sh`,
`claude plugin validate .`, plus each touched sub-repo's own
`scripts/check.sh`). Both specs' spec-completion reviews landed 0 findings
(evidence at `specs/agentprof-scrub-hex-tokens/evidence/spec-review.md` and
`specs/session-refresh-automation/evidence/spec-review.md`); untyped-agent-fanout's
review also 0 findings, scoped to exclude the interleaved
session-refresh-automation content it shares files with
(`specs/untyped-agent-fanout/evidence/spec-review.md`). Two low-value
`Status: draft` stubs were discovered and scaffolded under
session-refresh-automation (06 hook-test-path-robustness, 07
costsummary-comment-accuracy) — not yet triaged.

**Queue 5 (drained 2026-07-05)** — shared-viz-renderer (4 tasks: shared
`_shared/viz.py` renderer + golden tests; /workboard wired to
viz.timeline/viz.dag; byte-identical vendor into ~/agent-console with a
check.sh conformance gate, live service restarted; /fleet reference on the
emitted CSS block) and workboard-cli-graphs-health (4 tasks: CLI-sourced
liveness via `claude agents --json` + realpath attribution; resolve_dep DAG
edges; source-health markers; e2e + antigravity mirror + bump 0.8.5). All 8
`Status: done`, verifier PASS each, sequential drain, merged + pushed per
task. Spec pipeline ran in-session: critic NOT READY → amend → critic READY
→ breakdown → critic nits applied → drain. Two `Status: draft` stubs remain
under shared-viz-renderer (05 spec-note, 06 viz-axis tint) awaiting human
promotion — specs stay un-archived until those are triaged. Known
pre-existing red gate `tests/test_workboard_render.sh` (copy-button /
cwd-independence) predates the queue and is unchanged; not covered by any
spec — candidate for a follow-up fix task.

**Queue 4 (built + archived 2026-07-04)** — routing-merge-hardening: three
tasks (headless routing ladder, drain group-mode semantics, antigravity
autopilot ref) from the opus critic's NOT READY review of the
model-routing + /parallel-merge branch. All `Status: done`, spec verify
block green, critic re-run READY, moved to `specs/archive/`. **No active
specs remain under `specs/`.**

**Queue 3 (drained + archived 2026-07-04)** — the final three tasks:
completed-task-push 01 (push-on-completion, bump 0.7.12),
workboard-actionability 04 (Active-group reclassification, R10, bump 0.7.13),
and orchestrator-context 06 (needs-attention batons promoted to the inbox,
bump 0.7.14 — un-deferred and built the same session). All `Status: done`,
verifier PASS, pushed to origin/main. All four now-complete specs
(completed-task-push, workboard-actionability, workboard-copy-commands,
orchestrator-context) were moved to `specs/archive/`. **No active specs
remain under `specs/`** — the queue is empty. Queue 2's follow-ups and the
onboard-split-default tail landed earlier; the wave plan below is retained as
historical record.


Drain reads each task's `Depends on:` header (numbers within a spec,
across specs, paths relative to the task file
(../../<spec>/tasks/...)); this file is the human view of the same
graph. Per-spec Parallelization sections point here instead of
duplicating it.

**Queue 2 (current)** — the four 2026-07-03 follow-up specs:
drain-liveness-sweep (dls), orchestrator-context (oc), ultra-mode (um),
workflow-token-efficiency (wte). Ordering rationale: the drain skill
files are the contention point — dls 01 repairs the sweep semantics
first, then oc 01 adds the baton step, then um 02 adds the ultra
sections, then wte 03 retrofits tiers — one serial chain
(dls 01 → oc 01 → oc 02 → um 02 → wte 03 → wte 05); everything off
that chain parallelizes on disjoint Touch.

| Wave | Tasks (parallel within a wave) |
|---|---|
| 1 | dls 01; wte 01; wte 02 |
| 2 | oc 01; um 01 |
| 3 | oc 02; wte 04 |
| 4 | oc 03; oc 04 |
| 5 | um 02 |
| 6 | oc 05 |
| 7 | um 03 |
| 8 | wte 03 |
| 9 | wte 05 |
| 10 | osd 01 |

15 tasks. onboard-split-default (osd) joined 2026-07-03: one fused task
(skill + antigravity mirror + bump, per the same-commit mirror
convention) that serializes behind wte 05 solely on the plugin.json
bump chain — no queue-2 task touches the onboard skill files (verified
by Touch-header grep). Sequential drain follows this order automatically from the
Depends-on graph; waves 1, 2, 3, and 4 are the only sanctioned
concurrent groups (disjoint Touch, decision-uncoupled — the
decision-coupling test: dls/wte-01/wte-02 share no open naming or
interface choice; oc 01 and um 01 write to different files with formats
each spec pins; oc 02 and wte 04 likewise; oc 03 and oc 04 read task
01's baton grammar but write disjoint files). Version bumps are carried
by oc 05, um 03, and wte 05 (their specs each require one); dls 01
defers its bump to oc 05, the next bump on its chain. The bump tasks
are chained in the Depends-on headers themselves (oc 05 → um 03 →
wte 05), and um 02 depends on wte 01 (shared CLAUDE.md edits), so the
wave order above is machine-enforced, not prose-only.

Re-homed 2026-07-03: `specs/discovered-work-capture/tasks/01-discovered-work-capture.md`
(was `specs/beads-integration/tasks/01`). `Status: pending`; its dependencies
(chaining-antipatterns 01/03) are done — **dispatchable now** via /build or
/drain. The old beads-integration task 02 is withdrawn and that spec is closed.

**Queue 1 (drained 2026-07-03)** — 30 tasks across review-fixes,
model-agnostic, context-management, code-vs-llm, chaining-antipatterns,
repo-orientation, task-priority, tournament-votes, work-tracking, and
workflow-author: all `Status: done`, evidence under each spec's
`evidence/`, batch version bump 0.7.0 in review-fixes 99.
(beads-integration was removed from queue 1 by maintainer decision —
see docs/external-playbooks.md, Considered and rejected.)
