Status: draft
Discovered-from: specs/codebase-context-tree/evidence/capability-shakedown-2026-07-20.md
Spec: ../SPEC.md
Blocking: no

# ctx map ranking surfaces bash test locals above real API symbols

On a real repo (this toolkit's own tree), `ctx map`'s top entries are bash
test-scratch variables (`hooks.plugin-autorefresh.test.t#1`…`#10`) ranked
ahead of genuine classes/functions; the demo fixture ranks cleanly. The
ranking should down-weight `variable`-kind symbols — bash locals and
`#N`-suffixed duplicate names especially — relative to functions, classes,
and methods. (Capability-shakedown finding, 2026-07-20; vet/rewrite before
promoting.)

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
