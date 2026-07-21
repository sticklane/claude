Status: draft
Discovered-from: specs/agentprof-skill-audit/tasks/03-outcome-classification.md
Spec: ../SPEC.md
Blocking: no

# judge.Fake needs a per-call-sequenced Replies mode

The shared `internal/judge.Fake` supports only a single fixed `Reply`, so
task 03's 3-call generic-rubric aggregation tests needed a locally-scripted
judge instead. Task 04 (CLI wiring) will likely hit the same need; a
`Replies []string` mode on `judge.Fake` would let both tasks share one
fake implementation instead of each writing its own.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
