Status: draft
Discovered-from: 01-tool-and-model-durations.md
Spec: ../SPEC.md
Blocking: no

# Decide whether tool/pending leaves belong in the summary cost rollup

`-o summary` mode (`agentprof/summary.go`) derives "model" from the stack
leaf. After task 01 added `tool:<name>` and `tool:(pending)` leaves, summary
mode now emits zero-cost rows keyed `model=tool:<name>` /
`tool:(pending)`. This is harmless today (all summary tests still pass)
and may even be desired for the downstream weekly-cost view work
(specs/workboard-weekly-cost-view/), but needs a deliberate decision on
whether tool/pending leaves should be excluded from the (session, model)
cost rollup rather than left as an accidental side effect.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
