Status: obsolete
Closed: 2026-07-09 — resolved by fleet-viz-css-resync task 01 (commits 2f15b0d resync + 36215dc drift-guard test); `diff <(python3 .claude/skills/_shared/viz.py --emit-fleet-css) <(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' .claude/skills/fleet/reference.md)` is empty and tests/test_fleet_css_drift.sh passes.
Discovered-from: specs/shared-viz-renderer/tasks/06-viz-axis-muted-tint.md
Spec: ../SPEC.md
Blocking: no

# fleet/reference.md's embedded VIZ_CSS snapshot is stale after the viz-axis-muted-tint change

`fleet/reference.md`'s embedded VIZ_CSS snapshot (`.viz-axis div`, line 121) lacks the new `color: var(--viz-muted, #898781)` rule added by task 06, so `/fleet` renders the tint only after that snapshot is regenerated from `viz.py --emit-fleet-css`; that snapshot is task 04's territory (done/merged) and there is no automated sync gate catching this kind of drift.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
