# Task 04: Standalone cross-spec admission simulation script

Status: pending
Depends on: none
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirements R1, R2, R4, R5, R6, R12; the "Orchestrator-resolvable simulation" acceptance criterion)
Touch: tests/test_drain_swarm_admission.sh

## Goal

A new standalone script implements the greedy footprint-disjointness and
two-level-cap admission algorithm described in ../SPEC.md's R1/R2/R4/R5/R6/R12
as plain logic — no `/drain` invocation — and asserts every fixture case
the spec's acceptance criteria describe. This task is independent of tasks
01–03: the algorithm is fully specified in the spec itself, so this script
can be written directly from ../SPEC.md without waiting on the actual prose
landing in SKILL.md/reference.md.

## Touch

Only the new `tests/test_drain_swarm_admission.sh` file. Do not touch
`.claude/skills/drain/{SKILL.md,reference.md}` (task 01's scope),
`.claude/rules/token-discipline.md` (task 02's scope), or the mirror/plugin
files (task 03's scope).

## Steps

1. Read ../SPEC.md's Requirements (R1, R2, R4, R5, R6, R12) and the
   "Orchestrator-resolvable simulation" acceptance criterion in full — it
   specifies every fixture case this script must implement.
2. Write the failing test first: a fixture of 4 specs (3 mutually
   Touch-disjoint, plus a 4th overlapping one of them), each with
   dispatchable tasks, and assert before any implementation exists that the
   script fails/errors (nothing to run yet).
3. Implement the greedy footprint-disjointness claim algorithm (R1) and the
   task-level admission check (R2) as plain logic (bash functions/arrays —
   no `/drain` invocation, no dependency on the actual skill files' prose).
4. Assert fixture cases (a) and (b): all 3 mutually-disjoint specs admit
   simultaneously up to the cap (R1/R4); the 4th, overlapping spec is
   excluded from concurrent admission with its collision partner — only
   one of the colliding pair is ever admitted at a time (R5).
5. Add the degenerate-case fixture per R4: a 1-spec queue yields exactly 1
   claim, with no behavioral perturbation versus the single-spec path.
6. Assert fixture cases (c) and (d): two Touch-disjoint tasks in different,
   both-claimed specs (neither sharing a `Group:` line) both admit
   simultaneously (R2's cross-spec co-admissibility); two ungrouped tasks
   from the SAME spec, with no in-flight tasks in any other claimed spec,
   still do NOT co-admit, while an ungrouped task in one spec DOES admit
   while a task from a different spec is in flight — together proving
   "window empty" is scoped per-spec, not global.
7. Assert fixture case (e), the two-level cap throttle: 3 mutually-disjoint
   specs each offering 5 pairwise-disjoint-with-each-other dispatchable
   tasks (15 total candidates) — assert exactly 10 are admitted, and that
   no single spec is ever admitted more than its own `W` (≤5) worth of
   tasks, proving the shared ≤10 pool actually throttles the cross-spec sum
   rather than either a flat ≤10 window with no per-spec ceiling, or
   per-spec ceilings with no effective global throttle.
8. Confirm the script's own exit code is the runnable check (non-zero on
   any assertion failure); it does not require `/drain` or any other
   execution-stage skill to run.

## Acceptance

- [ ] `bash tests/test_drain_swarm_admission.sh` → exits 0
- [ ] The script contains distinct, separately-asserted fixture cases (a)–(e) as described above — not a single combined assertion that could pass with only some cases actually implemented. Runnable form (added 2026-07-19): on success the script's stdout names each case it asserted — `bash tests/test_drain_swarm_admission.sh | grep -o 'case ([a-e])' | sort -u | wc -l` → 5 (the script does not exist today, verified 2026-07-19, so this cannot pass vacuously)
- [ ] `test -f tests/test_drain_swarm_admission.sh` → file exists
