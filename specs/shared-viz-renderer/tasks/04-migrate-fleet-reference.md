# Task 04: Migrate the `/fleet` skill to the shared timeline CSS

Status: done
Depends on: 01
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R9)
Touch: /Users/sjaconette/claude/.claude/skills/fleet/reference.md

## Goal
The `/fleet` skill's timeline uses the shared structural CSS: its `reference.md` carries the `viz.py --emit-fleet-css` block verbatim between the sentinel markers, its TIMELINE ROWS markup + fill-rule prose are renamed to `.viz-*`, and fleet preserves its CVD-validated colors via `--viz-*` overrides in its own `:root`. All three dashboards then share identical structural rules.

## Touch
Only `fleet/reference.md`. Do NOT change `viz.py` (task 01 owns the emitted CSS) or `SKILL.md` unless it names timeline classes (then update it too, noting it in the commit). Fleet's `:root` palette override lives OUTSIDE the sentinel region so the emitted-block diff stays clean.

## Steps
1. Replace the timeline CSS region with the exact output of `python3 ~/claude/.claude/skills/_shared/viz.py --emit-fleet-css`, wrapped in the `/* >>> viz:timeline-css BEGIN/END */` sentinels.
2. Rename the TIMELINE ROWS markup + fill-rule prose (`reference.md:24-38,107-118,156-162`) from `.lane`/`.track`/`.bar`/`.axis` to their `.viz-*` equivalents.
3. Add a `:root` block (outside the sentinels) defining fleet's four validated `--viz-*` overrides (`running`, `done`←completed, `failed`, `open`←queued); leave `stale`/`blocked` to the shared fallback.

## Acceptance
- [x] `diff <(python3 /Users/sjaconette/claude/.claude/skills/_shared/viz.py --emit-fleet-css) <(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' /Users/sjaconette/claude/.claude/skills/fleet/reference.md)` → empty — verifier PASS, evidence: specs/shared-viz-renderer/evidence/04-migrate-fleet-reference.md
- [x] `! grep -nE 'class="(bar|lane|axis|track)[ "]' /Users/sjaconette/claude/.claude/skills/fleet/reference.md` → exits 0 (no old timeline classes remain) — verifier PASS, evidence: specs/shared-viz-renderer/evidence/04-migrate-fleet-reference.md
- [x] `grep -c 'viz:timeline-css BEGIN' /Users/sjaconette/claude/.claude/skills/fleet/reference.md` → `1` — verifier PASS, evidence: specs/shared-viz-renderer/evidence/04-migrate-fleet-reference.md

## Discovered

- [2026-07-04 /drain] Fill-rules prose never literally names `.lane`/`.track`/`.bar`/`.axis` as CSS class tokens (generic English nouns) — no rename applicable there; informational only, no stub.
- [2026-07-04 /drain] Shared `.viz-axis` rule drops the old `.axis div` `color: var(--muted)` tint — minor visual regression (axis labels inherit body ink); same tradeoff hits agent-console/workboard. → stub 06
