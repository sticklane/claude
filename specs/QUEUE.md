# Combined queue — wave plan (canonical, single copy)

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

Out of queue: `specs/beads-integration/tasks/01-discovered-work-capture.md`
(pending but requires maintainer re-homing as a standalone spec — see
its SPEC.md banner; not dispatchable); task 02 there is withdrawn.

**Queue 1 (drained 2026-07-03)** — 30 tasks across review-fixes,
model-agnostic, context-management, code-vs-llm, chaining-antipatterns,
repo-orientation, task-priority, tournament-votes, work-tracking, and
workflow-author: all `Status: done`, evidence under each spec's
`evidence/`, batch version bump 0.7.0 in review-fixes 99.
(beads-integration was removed from queue 1 by maintainer decision —
see docs/external-playbooks.md, Considered and rejected.)
