Status: done
Promotion-ready: true
Promoted-by-run: a219d53ef6bba100
Discovered-from: spec-completion review (specs/session-refresh-automation/evidence/spec-review.md)
Spec: ../SPEC.md
Blocking: no
Depends on: none
Budget: 3
Touch: agentprof/internal/costsummary/costsummary.go

# ReprimeCount comment: describe the main-loop-only filtering accurately

## Goal

Correct the doc comment on SessionStat's per-session reprime fields in
agentprof/internal/costsummary/costsummary.go so it states that per-session
reprime metrics count main-loop model calls only (samples carrying a
`calls` value and no agent frame) and names how that filtering differs from
the top-level Reprime rollup — instead of describing the fields as a strict
per-session slice of that rollup, which they are not. Comment-only change;
no behavior edits.

## Acceptance

- [x] `grep -c "per-session slice of the top-level Reprime rollup" agentprof/internal/costsummary/costsummary.go` returns 0 (the misleading phrase, present at line ~78 today, is gone). Evidence: command prints 0.
- [x] `grep -A2 "ReprimeCount and ReprimeCostMicrousd" agentprof/internal/costsummary/costsummary.go | grep -Eiq "main[- ]loop"` exits 0 (new wording names the main-loop-only filtering; no match today). Evidence: exit 0.
- [x] `cd agentprof && go test ./internal/costsummary/...` exits 0. Evidence: `ok github.com/sticklane/agentprof/internal/costsummary`; scripts/check.sh all green.
