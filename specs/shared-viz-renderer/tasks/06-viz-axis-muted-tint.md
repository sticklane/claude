Status: pending
Priority: P1
Discovered-from: specs/shared-viz-renderer/tasks/04-migrate-fleet-reference.md
Spec: ../SPEC.md
Blocking: no

# Restore muted axis-label tint in the shared viz CSS (or per-consumer override)

`.claude/skills/fleet/reference.md`'s `.viz-axis` rule (from the shared emitted CSS) drops the `color: var(--muted)` styling the old `.axis div` rule had — a minor visual regression (axis labels lose their muted-gray tint, inheriting body ink color instead) — inherent to adopting the shared structural block verbatim; worth a follow-up if visual parity matters, at agent-console/workboard's discretion since they hit the same tradeoff.

Decision (2026-07-06): restore the muted axis-label tint in the SHARED viz module (`.claude/skills/_shared/viz.py`'s VIZ_CSS) so every consumer gets it for free — a `var(--viz-muted, <hex>)` color rule on the `.viz-axis div` labels, per the spec's token convention. STATUS_HEX inline node/edge colors stay untouched. Cosmetic and cheap; applies uniformly to all consumers. Mirror to `antigravity/.agents/skills/_shared/viz.py` per CLAUDE.md's mirror convention.

## Acceptance

- [ ] `grep -q 'viz-muted' .claude/skills/_shared/viz.py` → exits 0 (muted axis rule present in the shared VIZ_CSS; currently absent)
- [ ] `grep -q 'viz-muted' antigravity/.agents/skills/_shared/viz.py` → exits 0 (mirror carries it)
- [ ] `python3 -m pytest .claude/skills/_shared/ .claude/skills/workboard/ -q` → all pass (existing consumer tests stay green)
