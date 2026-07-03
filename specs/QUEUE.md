# Combined queue — wave plan (canonical, single copy)

Drain reads each task's `Depends on:` header (numbers within a spec,
across specs, paths relative to the task file (../../<spec>/tasks/...)); this file is the human view of the
same graph. Per-spec Parallelization sections point here instead of
duplicating it.

Ordering rationale: review-fixes first (repairs the drain/evals/manifest
files everything else edits); docs/external-playbooks.md is appended by
five tasks, which therefore serialize; CLAUDE.md, token-discipline, the
drain files, and breakdown SKILL.md form the other serial chains.

| Wave | Tasks (parallel within a wave) |
|---|---|
| 1 | review-fixes 01, 02, 06; model-agnostic 01; context-management 03 |
| 2 | review-fixes 03; model-agnostic 03 |
| 3 | review-fixes 04 |
| 4 | review-fixes 05 |
| 5 | review-fixes 07 |
| 6 | review-fixes 08 |
| 7 | code-vs-llm 01 |
| 8 | model-agnostic 02 |
| 9 | context-management 01, 02 |
| 10 | context-management 04 |
| 11 | chaining-antipatterns 01 |
| 12 | chaining-antipatterns 02 |
| 13 | chaining-antipatterns 03 |
| 14 | model-agnostic 04 |
| 15 | repo-orientation 01; task-priority 01 |
| 16 | repo-orientation 02 |
| 17 | tournament-votes 01 |
| 18 | task-priority 02; workflow-author 01 |
| 19 | workflow-author 02 |
| 20 | work-tracking 01 |
| 21 | work-tracking 02 |
| 22 | review-fixes 99 (version bump + full-queue acceptance sweep) |

30 tasks. Sequential drain follows this order automatically from the
Depends-on graph; waves 1, 2, 9, 15, and 18 are the only sanctioned
concurrent groups (disjoint Touch, decision-uncoupled). The second
block (waves 15-21) is the session-two specs: orientation artifacts
first (new files), then the drain-file chain (tournament-votes →
work-tracking, the long pole), research-record appends serialized
throughout (repo-orientation 02 → tournament-votes 01 →
task-priority 02 → workflow-author 02 → work-tracking 02).
(beads-integration removed by maintainer decision — see
docs/external-playbooks.md, Considered and rejected.)
