# Combined queue — wave plan (canonical, single copy)

Drain reads each task's `Depends on:` header (numbers within a spec,
repo-relative paths across specs); this file is the human view of the
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
| 14 | beads-integration 01; model-agnostic 04 |
| 15 | beads-integration 02 |
| 16 | review-fixes 99 (version bump + full-queue acceptance sweep) |

23 tasks. Sequential drain follows this order automatically from the
Depends-on graph; waves 1, 2, 9, and 14 are the only sanctioned
concurrent groups (disjoint Touch, decision-uncoupled).
