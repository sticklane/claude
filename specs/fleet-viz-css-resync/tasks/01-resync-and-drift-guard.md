# Task 01: Resync /fleet's CSS and add a drift guard

Status: done
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

- [x] `diff <(python3 .claude/skills/_shared/viz.py --emit-fleet-css) <(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' .claude/skills/fleet/reference.md)` → empty
  - Evidence: diff empty (exit 0); byte-identical. See evidence/01-resync-and-drift-guard.md (C1).
- [x] `bash tests/test_fleet_css_drift.sh` → exits 0 (post-resync)
  - Evidence: exit 0, no output; red against pre-resync state (exit 1). evidence/01-resync-and-drift-guard.md (C2, C3).
- [x] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` → all pass, including the new test, with no runner changes
  - Evidence: new test passes and is picked up by the glob, no runner changes. 3 unrelated tests (drain_owner_protocol, hook_templates, install_gates) fail on GNU-vs-BSD sed/stat + root-permission env — verified identical on base 6196cc8, i.e. pre-existing, not regressions. evidence/01-resync-and-drift-guard.md.
- [x] `git diff .claude-plugin/plugin.json` → shows a one-patch-level version bump
  - Evidence: 0.8.23 -> 0.8.24. evidence/01-resync-and-drift-guard.md (C4).

## Next stage

No further tasks in this spec.

## Discovered

- Protect fleet reference.md's viz-css block from the prettier format hook (stub 02-prettierignore-viz-css.md)
- Make the three container-hostile tests portable (GNU sed/stat, root) (stub 03-container-portable-tests.md)
