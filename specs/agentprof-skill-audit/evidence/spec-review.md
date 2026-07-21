spec review: 2 findings surfaced, 0 fixed, 0 discovered

Diff base: 8ea2d7ebf791047840dabb7ee6a08114457cc403 (first `drain:
agentprof-skill-audit task .* in-progress` commit) through origin/main
(27561220 at review time), restricted to the spec's union Touch. 878 new
non-test product lines across `cmd_skillcheck.go`, `cmd_skillcheck_trigger.go`,
`cmd_skillcheck_outcome.go`, `main.go`.

Findings:

1. `cmd_skillcheck.go:220-229` / `cmd_skillcheck_trigger.go:161` —
   `DetectPossibleMisses` over-reports possible-misses (flags a matching
   user turn without checking whether the skill actually fired that
   session). High-confidence, but not fixed and not newly discovered:
   already tracked as `specs/agentprof-skill-audit/tasks/08-possible-miss-false-positive-check.md`
   (draft stub, deliberately deferred with its own acceptance criteria).
   Fixing on this review branch would pre-empt scoped future work.
2. `cmd_skillcheck.go:246-256` — `scoreOutcome` returns `scored=false` on
   any `ClassifyOutcome` error, conflating a genuine failure with the
   documented benign SKILL.md-removal race. Confidence 70, below the
   high-confidence bar (reads as an intentional fail-open) — excluded per
   the finding filter, not fixed, not discovered.

No fixes applied; no commits beyond the reviewed origin/main tip. No
union-Touch or tasks/ files touched. Gate re-run unnecessary (zero fixes;
tasks 01-04 already passed their own gates).
