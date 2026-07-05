# Task 06: cross-check baton-adoption predicate grammar against drain reference.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: draft
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

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
