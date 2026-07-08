# Resync /fleet's CSS with viz.py and prevent future drift

## Problem

`/fleet`'s `reference.md` carries a copied timeline-CSS block that was
supposed to stay byte-identical to `viz.py --emit-fleet-css`'s output (this
was the entire premise of `shared-viz-renderer/04-migrate-fleet-reference.md`,
already marked done). It has since drifted: a later task in the same spec
(06, "restore muted axis-label tint") added
`color: var(--viz-muted, #898781)` to `.viz-axis div` in `viz.py`'s emitted
CSS and bumped its embedded sha256 header, but never touched
`fleet/reference.md`'s copy.

Found during a runtime verification sweep (2026-07-06) via a direct `diff`
between `python3 .claude/skills/_shared/viz.py --emit-fleet-css` and the
`viz:timeline-css BEGIN`/`END` block in `fleet/reference.md` — this is not
stale documentation, it's a live content mismatch: `/fleet`'s rendered
timeline is missing the muted axis-label tint right now.

Nothing currently enforces the byte-identity the spec was built to
guarantee — task 04's own acceptance criteria checked for it once at
landing time but there's no ongoing gate, so any future `viz.py` CSS change
will silently drift `/fleet` out of sync again, exactly as happened here.

## Solution

1. Resync `fleet/reference.md`'s CSS block from the current
   `viz.py --emit-fleet-css` output.
2. Add `tests/test_fleet_css_drift.sh`, a shell gate script modeled
   directly on the existing `tests/test_antigravity_parity.sh` (the
   established precedent for a mechanical drift/mirror-conformance gate in
   this repo), that runs the same `diff` this spec's acceptance criteria
   use and fails loudly if `fleet/reference.md`'s CSS block ever diverges
   from `viz.py --emit-fleet-css` again.

No antigravity fleet mirror exists — `antigravity/README.md` explicitly
exempts `/fleet` ("Not ported — Antigravity's Agent Manager is this surface
natively"), and no `reference.md`/`viz:timeline-css` content exists anywhere
under `antigravity/`. Nothing to sync there.

## Requirements

R1: `fleet/reference.md`'s `viz:timeline-css BEGIN`/`END` block is
byte-identical to `python3 .claude/skills/_shared/viz.py --emit-fleet-css`'s
current output.

R2: `tests/test_fleet_css_drift.sh` exists, modeled on
`tests/test_antigravity_parity.sh`'s structure, and fails (non-zero exit,
naming the mismatch) if `fleet/reference.md`'s CSS block and
`viz.py --emit-fleet-css`'s live output ever diverge. It is a plain shell
script under `tests/` — not a pytest file under `.claude/skills/_shared/` —
so it's automatically picked up by the repo's only test sweep
(`for t in tests/test_*.sh; do bash "$t"; done`, per `AGENTS.md`) with no
runner changes.

R4: `.claude-plugin/plugin.json`'s `version` is bumped one patch level, per
CLAUDE.md's "Bump `version` in `plugin.json` whenever skill behavior
changes" — the resync changes `/fleet`'s rendered output (the muted axis
tint becomes visible), which counts as a skill-behavior change even though
no `.claude/skills/` file logic changed, only a reference asset.

R3: No antigravity mirror sync is needed for this spec — confirmed `/fleet`
is `Not ported` in `antigravity/README.md` and no fleet-related content
exists under `antigravity/`. (If a future spec adds an antigravity fleet
mirror, that spec is responsible for its own CSS-drift guard; this one
isn't extended to cover it.)

## Out of scope

- Fixing `shared-viz-renderer/03-vendor-into-agent-console.md`'s separate,
  already-logged finding (architecture superseded by a dynamic-import
  migration) — that's tracked independently, not part of this CSS resync.
- Any change to `viz.py`'s actual CSS output/styling — this spec only
  resyncs the copy and adds the drift guard, it does not alter what the
  timeline looks like.

## Acceptance criteria

- [ ] `diff <(python3 .claude/skills/_shared/viz.py --emit-fleet-css) <(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' .claude/skills/fleet/reference.md)`
      is empty.
- [ ] `bash tests/test_fleet_css_drift.sh` fails when run against the
      pre-fix state (verify by temporarily reverting the resync and
      confirming red, then re-applying and confirming green — a real
      red/green cycle, not just a green test).
- [ ] `tests/test_fleet_css_drift.sh` is picked up automatically by
      `for t in tests/test_*.sh; do bash "$t"; done` with no runner changes.
- [ ] The full `tests/test_*.sh` sweep remains green.
- [ ] `.claude-plugin/plugin.json`'s `version` is bumped one patch level in
      the same commit.

## Open questions

None — test location/format (shell script under `tests/`, modeled on
`test_antigravity_parity.sh`) and antigravity mirror scope (none needed) are
both resolved above.

## Parallelization

Single-track. `tasks/01-resync-and-drift-guard.md` covers R1, R2, R4
end-to-end; no parallel groups.
