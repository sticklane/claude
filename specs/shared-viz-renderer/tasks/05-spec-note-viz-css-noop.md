Status: in-progress
Priority: P1
Discovered-from: specs/shared-viz-renderer/tasks/01-extract-viz-module.md
Spec: ../SPEC.md
Blocking: no

# Document the VIZ_CSS .viz-node/.viz-edge intentional no-op in SPEC.md

The task's Steps text calls for VIZ_CSS to cover `.viz-node`/`.viz-edge` structurally, but giving them real CSS declarations would let the cascade override the per-node inline STATUS_HEX stroke/fill colors that dag() relies on — documented as an intentional no-op with a comment in viz.py rather than filed as a gap, since no acceptance criterion tests it and it's consistent with the spec's "SVG colors via inline hex" design; worth a one-line note in SPEC.md if a future consumer (task 03/04) expects real rules there.

Decision (2026-07-06): yes — document the intentional VIZ_CSS no-op in specs/shared-viz-renderer/SPEC.md: `.viz-node`/`.viz-edge` are deliberately left unstyled so the cascade cannot override the per-node inline STATUS_HEX stroke/fill colors that dag() emits.

## Acceptance

- [ ] `grep -qi 'no-op' specs/shared-viz-renderer/SPEC.md` → exits 0 (the note exists; currently absent)
- [ ] `grep -i -C2 'no-op' specs/shared-viz-renderer/SPEC.md | grep -q 'viz-node'` → exits 0 (the note names the unstyled classes)
