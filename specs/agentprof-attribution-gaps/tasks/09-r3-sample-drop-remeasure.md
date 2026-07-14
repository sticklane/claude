# Task 09: re-measure R3's sample-drop claim against real data

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Discovered-from: 2026-07-13 independent verification sweep
Depends on: 08
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R3)
Touch: agentprof/internal/claude/, specs/agentprof-attribution-gaps/evidence/, specs/agentprof-attribution-gaps/SPEC.md

## Goal

The 2026-07-13 verification sweep measured R3's spec-level claim —
empty-values `tool:(pending)` samples = 0 AND total sample count drops
≥8% on the full local 14-day window vs the pre-change parser at b4971fe —
against real ~/.claude data, and the ≥8% drop does NOT hold (tasks 03/08
had honestly marked this measurement MANUAL-PENDING from their isolated
worktrees). Reproduce the measurement, determine why the pending-sample
consolidation didn't reduce total samples as projected, and either fix
the parser or re-scope R3 with an explicit maintainer decision recorded
in SPEC.md.

## Steps

1. Reproduce the sweep's measurement: run the current parser and the
   pre-change parser at b4971fe over the same local 14-day ~/.claude
   window; record empty-values pending count and total sample counts
   for both in evidence/.
2. Diagnose why the consolidation didn't produce the projected ≥8%
   total-sample drop (e.g. the 03/08 fixes matched results that
   previously landed pending, so consolidation had fewer samples to
   collapse than the original 8,854-sample estimate assumed).
3. Either fix the parser so R3's numbers hold, or formally amend R3 in
   SPEC.md with an explicit maintainer decision re-scoping the criterion
   to what the data supports.

## Acceptance

- [x] evidence/09-r3-remeasure.md records the re-measured numbers
      (before/after empty-values pending count and total sample counts on
      the full local 14-day window vs b4971fe, commands included)
      — evidence/09-r3-remeasure.md: b4971fe 131,521 total / 11,663 empty
      pending; current 131,519 total / 0 empty pending (4 with pending_calls);
      commands included.
- [x] R3 either passes as written against the re-measured numbers, or
      SPEC.md carries a formal amendment to R3 citing an explicit maintainer
      decision and evidence/09-r3-remeasure.md
      — SPEC.md R3 requirement note + acceptance criterion carry the
      2026-07-13 (task 09) maintainer decision striking the ≥8%-drop clause
      (actual 0.0015%) and citing evidence/09-r3-remeasure.md; empty-values=0
      half stands and passes.
- [x] `cd agentprof && go test ./...` → pass; `bash agentprof/scripts/check.sh`
      → green (unchanged if no parser fix was needed)
      — go test ./... all ok; check.sh: format-check ok, lint ok, tests ok.
      No parser change made.
