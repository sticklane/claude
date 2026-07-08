Status: draft
Discovered-from: specs/shared-viz-renderer/tasks/06-viz-axis-muted-tint.md
Spec: ../SPEC.md
Blocking: no

# fleet/reference.md's embedded VIZ_CSS snapshot is stale after the viz-axis-muted-tint change

`fleet/reference.md`'s embedded VIZ_CSS snapshot (`.viz-axis div`, line 121) lacks the new `color: var(--viz-muted, #898781)` rule added by task 06, so `/fleet` renders the tint only after that snapshot is regenerated from `viz.py --emit-fleet-css`; that snapshot is task 04's territory (done/merged) and there is no automated sync gate catching this kind of drift.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
