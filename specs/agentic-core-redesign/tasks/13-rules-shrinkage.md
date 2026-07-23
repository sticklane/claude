# Task 13: rules shrinkage — mechanize, keep, or delete every rule line

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 10, 11
Priority: P3
Budget: 20 turns
Spec: ../SPEC.md (D2; Migration step 8)
Touch: .claude/rules/, CLAUDE.md, docs/rules-triage.md

## Goal

Every line of `.claude/rules/` and CLAUDE.md's rule-like conventions is
classified in `docs/rules-triage.md` — `mechanized` (names the code/test
that now enforces it), `kept` (judgment or context-management guidance),
or `deleted` (dead letter) — and the files are edited to match. The
end state approximates: untrusted-data, context-management guidance, and
pointers to `agentic`.

## Touch

The untrusted-data rule is kept verbatim. Anything a prior task already
mechanized (locks, sync, caps, screen, schemas, tiers-in-config) must be
classified `mechanized` with the enforcing path named — classifying it
`kept` is a defect.

## Steps

1. Build the triage table rule-file by rule-file; for each `mechanized`
   row, name the enforcing artifact and verify it exists.
2. Apply the edits: delete `deleted` rows' text, shrink `kept` files to
   their surviving content, update CLAUDE.md references.
3. Run the full suite; fix any doc-link tests.

## Acceptance

- [x] `bash -c 'bad=$(grep -c "· mechanized ·.*<none>" docs/rules-triage.md); echo $bad'` → `0` (every mechanized row names its enforcing path)
- [x] `bash -c 'for p in $(grep "· mechanized ·" docs/rules-triage.md | sed "s/.*· mechanized · //" | cut -d" " -f1); do [ -e "$p" ] || echo "missing: $p"; done'` → no output (named enforcers exist)
- [x] `test -f .claude/rules/untrusted-data.md && echo KEPT` → `KEPT`
- [x] `bash tests/test_doc_links.sh && bash scripts/check.sh` → green after the deletions

Depth ceiling: L1 — the keep/delete judgments are editorial; the
behavioral complement is a maintainer read of docs/rules-triage.md, plus
the audit job (task 12) catching any mechanized rule that regresses in
practice.
