# Task 01: model-free owner/CAS protocol test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirement R9; grammar pinned in Solution "DRAIN-OWNER.md format")
Touch: tests/test_drain_owner_protocol.sh

## Goal

`tests/test_drain_owner_protocol.sh` exists and passes: a self-contained
bash test that builds a throwaway git repo under `mktemp -d` and proves
the coordination protocol's git mechanics, using the exact grammar the
spec pins (owner headers `Run-token:`/`Host:`/`Started:`/`Generation:`/
`Spec:`; flip line `Status: pending` → `Status: in-progress`). Five
cases: (a) CAS flip — after a simulated foreign flip, an exact-match
replacement of `Status: pending` fails and grep confirms a single
in-progress writer; (b) owner lifecycle — claim commit, generation
update, release commit leave expected file states; (c) path-scoped
commit — a staged foreign file does not ride along; (d) losing claim —
two sequential claim commits with different Run-tokens, read-back at
HEAD identifies exactly one winner, loser's token absent; (e) baton
adoption predicate — matching `Run-token:` lines in fixture baton +
owner pass, mismatched fail, via the documented one-liner comparison.

## Touch

Only the new test file. Do NOT edit any skill files (tasks 02–04 own
those), other tests, or the gate wiring — `tests/test_*.sh` naming makes
the existing gate pick it up automatically. The test must not depend on
skill text existing (it validates protocol mechanics from the spec's
pinned grammar, so it stays green regardless of task 02–04 ordering).

## Steps

1. Write the failing skeleton first: the five case functions with a
   `fail=1` default, confirm the script fails, then implement case by
   case.
2. Follow the existing tests' conventions (see any sibling
   `tests/test_*.sh` for the pass/fail output shape); temp repo per
   case or one repo reused with cleanup trap.
3. All five cases green; run the full `for t in tests/test_*.sh` sweep
   to confirm no interference; commit.

## Acceptance

- [x] `bash tests/test_drain_owner_protocol.sh` → exit 0, output names all five cases (a–e) as PASS
      Evidence: verifier confirmed exit 0, 13/13 assertions, all five cases printed PASS — specs/multi-session-coordination/evidence/01-owner-protocol-test.md
- [x] `grep -c "Run-token" tests/test_drain_owner_protocol.sh` → ≥ 2 (claim-race + adoption cases use the pinned grammar)
      Evidence: verifier confirmed count = 18 — specs/multi-session-coordination/evidence/01-owner-protocol-test.md
- [x] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` → exit 0
      Evidence: verifier confirmed the full sweep exits 0 — specs/multi-session-coordination/evidence/01-owner-protocol-test.md
- [x] `git diff --name-only main` → only `tests/test_drain_owner_protocol.sh` (plus this task file)
      Evidence: verifier confirmed diff scope is exactly this file — specs/multi-session-coordination/evidence/01-owner-protocol-test.md

## Discovered

- SPEC.md's R2 "documented one-liner" baton-adoption predicate is not yet
  implemented anywhere in `.claude/skills/drain/reference.md` — task 02
  owns landing that text; this task's case (e) reimplements the predicate
  locally per its own Touch constraint ("must not depend on skill text
  existing"), so it won't catch a future divergence between the real
  skill code and the spec's grammar. See task 06.
