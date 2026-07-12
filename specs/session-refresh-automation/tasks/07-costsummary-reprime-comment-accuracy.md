Status: draft
Discovered-from: spec-completion review (specs/session-refresh-automation/evidence/spec-review.md)
Spec: ../SPEC.md
Blocking: no

# ReprimeCount comment overstates it as a strict slice of the rollup

agentprof/internal/costsummary/costsummary.go's comment on the per-session
`ReprimeCount` field calls it "the per-session slice of the top-level
Reprime rollup", but the top-level rollup counts reprime samples with any
agent frame while the per-session aggregation excludes subagent/no-`calls`
samples — the two are not strict slices of each other. The per-session
main-loop-only behavior is likely the intended one for the wake budget;
this is a comment-accuracy nit, not a correctness bug.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
