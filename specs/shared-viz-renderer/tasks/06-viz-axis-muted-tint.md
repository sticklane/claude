Status: draft
Priority: P1
Discovered-from: specs/shared-viz-renderer/tasks/04-migrate-fleet-reference.md
Spec: ../SPEC.md
Blocking: no

# Restore muted axis-label tint in the shared viz CSS (or per-consumer override)

`.claude/skills/fleet/reference.md`'s `.viz-axis` rule (from the shared emitted CSS) drops the `color: var(--muted)` styling the old `.axis div` rule had — a minor visual regression (axis labels lose their muted-gray tint, inheriting body ink color instead) — inherent to adopting the shared structural block verbatim; worth a follow-up if visual parity matters, at agent-console/workboard's discretion since they hit the same tradeoff.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
