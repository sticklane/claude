Status: done
Priority: P1
Discovered-from: specs/shared-viz-renderer/tasks/04-migrate-fleet-reference.md
Spec: ../SPEC.md
Blocking: no

# Restore muted axis-label tint in the shared viz CSS (or per-consumer override)

`.claude/skills/fleet/reference.md`'s `.viz-axis` rule (from the shared emitted CSS) drops the `color: var(--muted)` styling the old `.axis div` rule had — a minor visual regression (axis labels lose their muted-gray tint, inheriting body ink color instead) — inherent to adopting the shared structural block verbatim; worth a follow-up if visual parity matters, at agent-console/workboard's discretion since they hit the same tradeoff.

Decision (2026-07-06): restore the muted axis-label tint in the SHARED viz module (`.claude/skills/_shared/viz.py`'s VIZ_CSS) so every consumer gets it for free — a `var(--viz-muted, <hex>)` color rule on the `.viz-axis div` labels, per the spec's token convention. STATUS_HEX inline node/edge colors stay untouched. Cosmetic and cheap; applies uniformly to all consumers. Mirror to `antigravity/.agents/skills/_shared/viz.py` per CLAUDE.md's mirror convention.

## Acceptance

- [x] `grep -q 'viz-muted' .claude/skills/_shared/viz.py` → exits 0 (muted axis rule present in the shared VIZ_CSS; currently absent) — `.viz-axis div` now sets `color: var(--viz-muted, #898781)` — verifier PASS (2026-07-16 sweep)
- [x] `grep -q 'viz-muted' antigravity/.agents/skills/_shared/viz.py` → exits 0 (mirror carries it) — byte-identical mirror copied same commit — verifier PASS (2026-07-16 sweep)
- [x] `python3 -m pytest .claude/skills/_shared/ .claude/skills/workboard/ -q` → all pass (existing consumer tests stay green) — 116 passed — verifier PASS (2026-07-16 sweep)

## Discovered

- `fleet/reference.md`'s embedded VIZ_CSS snapshot (`.viz-axis div`, line 121) is now stale — it lacks the new color rule, so /fleet renders the tint only after that snapshot is regenerated from `viz.py --emit-fleet-css`; that snapshot is task 04's territory (done/merged) and there is no automated sync gate catching the drift.
- `plugin.json` version was not bumped for this skill-behavior change (emitted VIZ_CSS changed); CLAUDE.md places the shared-viz spec's mirror + `plugin.json` bump in a task's `Touch:` (a closing task), but task 06 has no `Touch:` line and no closing task follows it in `specs/shared-viz-renderer/tasks/`, so the spec-wide bump may be missing.
- Pre-existing formatting drift: HEAD's `.claude/skills/_shared/viz.py` (and its antigravity mirror) are not `ruff format`-clean, the repo's own declared canonical Python formatter (`.claude/hooks/post-tool-format.sh`, SPEC R11) would reflow them.
