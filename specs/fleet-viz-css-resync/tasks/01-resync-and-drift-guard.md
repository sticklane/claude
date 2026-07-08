# Task 01: Resync /fleet's CSS and add a drift guard

Status: in-progress
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2, R4)
Touch: .claude/skills/fleet/reference.md, tests/test_fleet_css_drift.sh, .claude-plugin/plugin.json

## Goal

`fleet/reference.md`'s `viz:timeline-css BEGIN`/`END` block is
byte-identical to `viz.py --emit-fleet-css`'s current output. A new
`tests/test_fleet_css_drift.sh`, modeled on `tests/test_antigravity_parity.sh`,
fails loudly if they ever diverge again, and is picked up automatically by
the repo's `test_*.sh` sweep. `plugin.json`'s version is bumped.

## Touch

Do not touch `.claude/skills/_shared/viz.py` — this task only resyncs the
copy in `fleet/reference.md`, it does not change what `viz.py` emits. Do
not add anything under `antigravity/` — confirmed no fleet mirror exists
there (see SPEC.md's Solution section); nothing to sync.

## Steps

1. Run `python3 .claude/skills/_shared/viz.py --emit-fleet-css` and diff it
   against `fleet/reference.md`'s current `viz:timeline-css BEGIN`/`END`
   block — confirm the one-line mismatch (missing muted axis-label tint).
2. Read `tests/test_antigravity_parity.sh` to use as the structural model.
3. Write `tests/test_fleet_css_drift.sh`: runs the same diff as step 1,
   exits non-zero and names the mismatch if the two differ, exits 0 if they
   match.
4. Confirm the new test fails against the current (pre-resync) state — a
   real red run, not assumed.
5. Resync `fleet/reference.md`'s CSS block from `viz.py --emit-fleet-css`'s
   current output.
6. Confirm the new test now passes (green).
7. Bump `.claude-plugin/plugin.json`'s `version` one patch level.

## Acceptance

- [ ] `diff <(python3 .claude/skills/_shared/viz.py --emit-fleet-css) <(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' .claude/skills/fleet/reference.md)` → empty
- [ ] `bash tests/test_fleet_css_drift.sh` → exits 0 (post-resync)
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` → all pass, including the new test, with no runner changes
- [ ] `git diff .claude-plugin/plugin.json` → shows a one-patch-level version bump

## Next stage

No further tasks in this spec.
