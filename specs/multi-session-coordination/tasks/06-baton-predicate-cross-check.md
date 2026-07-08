# Task 06: cross-check baton-adoption predicate grammar against drain reference.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Discovered-from: specs/multi-session-coordination/tasks/01-owner-protocol-test.md
Spec: ../SPEC.md
Blocking: no

# Cross-check baton-adoption predicate grammar against drain reference.md

Task 01's test case (e) reimplements the R2 "documented one-liner"
baton-adoption predicate locally (its Touch constraint forbids depending on
skill text existing). Task 02 lands the real predicate text in
`.claude/skills/drain/reference.md`. Once task 02 ships, verify the two
grammars match — otherwise the test can pass while the shipped skill text
diverges from the spec's pinned grammar, silently.

Decision (2026-07-06): task 02 is done — the predicate shipped in
`.claude/skills/drain/reference.md` (the R2 baton-lineage exception: adopt
iff the baton's `Run-token:` line matches DRAIN-OWNER.md's). Proceed: make
the task-01 test's case (e) read/assert against the SHIPPED reference text
(or add a cross-check assertion that the local predicate and the shipped
text agree), so divergence fails the suite instead of passing silently.

## Acceptance

- [x] `grep -q 'skills/drain/reference.md' tests/test_drain_owner_protocol.sh` → exits 0 (the test now cross-checks against the shipped reference text; currently 0 mentions) — verifier: exit 0; new `REFERENCE_MD="$SCRIPT_DIR/../.claude/skills/drain/reference.md"` line matches (evidence/06-baton-predicate-cross-check.md)
- [x] `bash tests/test_drain_owner_protocol.sh` → all cases pass, `fail: 0` (suite stays green with the cross-check added) — verifier: all five cases (a)-(e) PASS, `pass: 15 fail: 0`, exit 0; mutating the shipped predicate makes case (e) fail (`pass: 14 fail: 1`), proving the cross-check binds (evidence/06-baton-predicate-cross-check.md)
