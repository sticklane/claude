# Task 14: Cross-subsystem integration and end-to-end acceptance

Status: pending
Depends on: 13
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R1, R2, R13, R17; contracts C3, C4)
Touch: context-tree/tests/e2e/**, context-tree/tests/*.rs

## Goal

The full documented check command (`bash context-tree/scripts/check.sh`)
runs green with every subsystem wired together, and the acceptance
criteria that genuinely span multiple subsystems — ones no single earlier
task could complete alone — are covered by new integration tests. This
task adds tests only; it must not need to change `src/` (if it does,
that's a signal an earlier task's contract was incomplete — fix the
earlier task's module directly rather than patching around it here, and
note the gap in the final report).

## Touch

Only `tests/e2e/**` and new top-level integration test files under
`tests/`. Do not modify any `src/` file.

## Steps

1. Mid-edit robustness integration test (R1/R13, spans extraction +
   query + notes + re-anchoring): given a fixture file with a mid-function
   syntax error, assert in one test: (a) sibling symbols in the same file
   still list via `ctx tree`; (b) `ctx at` on the broken span resolves to
   the module fallback without error; (c) a note anchored to an untouched
   sibling keeps its freshness; (d) no re-anchoring fires for the
   parse-failed file (task 10 already unit-tests this in isolation — this
   test exercises it inside a full sync+query+notes flow); (e) a note
   anchored to the BROKEN symbol reads stale while broken, its anchor
   binding untouched, and re-derives fresh after repair; (f) repairing the
   error restores full facts on the next sync.
2. `--json` aggregate test: for each of tree/sig/map/deps/refs/at, the
   `--json` variant pipes through `jq .` with exit 0 and contains an
   asserted key for that verb's payload — a single test iterating all six
   verbs against one shared fixture (tasks 06/07 already test this
   per-command; this test is the cross-verb consistency check).
3. End-to-end user-flow script (the CUJS.md CUJ0/thesis walkthrough): on a
   fixture repo containing at least 3 of the 12 languages, drive `ctx
init` -> `ctx map` -> `ctx sig` -> `ctx notes add` -> (perform a
   refactor on the noted symbol) -> assert the note's stale flag -> `ctx
notes list --stale` shows it. Implement as one shell or Rust
   integration test script under `tests/e2e/`.
4. Run the full documented check command and fix any integration-only
   failures surfaced by running every subsystem together (flaky ordering,
   shared fixture collisions, etc.) — but do not touch `src/` logic; if a
   genuine `src/` bug surfaces here, it means an earlier task's own tests
   under-covered its contract, so fix it in that module and note which
   task's coverage gap it was in the final report.

## Acceptance

- [ ] `cd context-tree && cargo test mid_edit_robustness` → passes (all
      six sub-assertions in Steps 1)
- [ ] `cd context-tree && cargo test json_all_verbs` → passes (six verbs,
      each piping through `jq .` with exit 0 and an asserted key)
- [ ] `cd context-tree && cargo test e2e_user_flow` → passes (init -> map
      -> sig -> notes add -> refactor -> stale -> notes list --stale, on a
      ≥3-language fixture)
- [ ] `bash context-tree/scripts/check.sh` → exits 0 (full suite green,
      the umbrella criterion covering R1/R4/R5/R6-R10/R19/R12/R14/R18
      together with all prior tasks' own coverage)
