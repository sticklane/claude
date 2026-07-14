Status: obsolete
Closed: gate-confirmed 2026-07-14 (drain gen 3, Run-token c92aedb1ae49f8d3) — tasks 02, 04, and 05's acceptance criteria (specs/skill-doc-size-guards/tasks/{02-non-drain-reference-toc-headings,04-wire-gate-and-mirror-drain,05-final-gate-verification}.md) use boolean membership checks, non-empty diffs, a re-read-live version comparison (04 AC3 / 05 AC6 explicitly avoid hard-coding), and a forward bound (05 AC2 ≤ 500, satisfied post-task-03) — none carry a stale pre-task-03 numeric snapshot the way task 01's ACs 3-4 did. The risk this stub flagged did not materialize in the remaining tasks.
Discovered-from: specs/skill-doc-size-guards/tasks/01-lint-skill-size-gate-script.md
Spec: ../SPEC.md
Blocking: no

# Recheck remaining spec tasks for stale pre-task-03 counts/expectations

Task 01's acceptance criteria 3 and 4 anchored on a codebase snapshot
(drain/SKILL.md at 517 lines, 8 reference.md TOC gaps) that this same
drain run's task 03 already resolved before task 01 dispatched, leaving
those two criteria stale (correctly un-satisfiable as literally written,
though the underlying implementation was verified correct for current
reality). The spec's remaining tasks (02, 04, 05) may carry similar
counts or expectations tied to that same pre-task-03 snapshot — worth a
pass confirming their acceptance criteria still match current reality
before treating their gates as final.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
