# Task 05: Spec note — pure tool: samples have no explicit "no model" bucket

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P3
Budget: 2 turns
Spec: ../SPEC.md
Discovered-from: specs/workboard-weekly-cost-view/tasks/02-summary-flag.md
Touch: specs/workboard-weekly-cost-view/SPEC.md

## Goal

`specs/workboard-weekly-cost-view/SPEC.md` carries an explanatory NOTE
(add a note; change NO requirement — R3's semantics stay exactly as
shipped) documenting that pure `tool:` samples (only `duration_ms`, no
tokens/cost) resolve their model to the preceding non-tool frame (e.g.
`main`) under the R3 leaf rule, so their duration lands in
`by_model["main"]` — harmless for the cost panel today, but worth naming
once agentprof-instrumentation's richer tool/duration frames ship, since
the contract has no explicit "no model" bucket.

## Steps

1. Add the note adjacent to the R3 model-derivation rule in SPEC.md.

## Acceptance

- [ ] `grep -Eqi 'no.model' specs/workboard-weekly-cost-view/SPEC.md` → match
- [ ] `grep -qi 'duration_ms' specs/workboard-weekly-cost-view/SPEC.md` → match (note names what lands mis-bucketed)
- [ ] `cd agentprof && go test ./internal/costsummary/` → pass (docs-only change; code untouched)
