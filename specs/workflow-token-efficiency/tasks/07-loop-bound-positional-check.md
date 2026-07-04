# Task 07: constrain loop-bound numeral position in bin/check-token-discipline

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: none
Spec: ../SPEC.md
Discovered-by: 02-conformance-checker.md

## Goal

verbatim worker report — vet/rewrite before promoting:

> Loop-bound numeral is positionally unconstrained in
> `bin/check-token-discipline` (`is_live_loop`/`LBOUND`) — any digit 1–4
> anywhere in a loop paragraph satisfies the bound (e.g. an unbounded
> `retry` paragraph that also says "2k tokens" passes); this is
> spec-compliant (SPEC R6 lists "a numeral 1–4" as a bound with no
> position rule, and the tests are the contract) but is a false-negative
> risk the task-03 retrofit should be aware of when adding bounds.

## Resolution (done)

`LBOUND` in `bin/check-token-discipline` now accepts a count (digit 1-4 or
spelled one/two/three/four/single) as a bound only in a counting context —
quantifier+count, count+word-anchored-cycle-noun (optionally a range), once/twice,
or a named generation cap — so a bare stray numeral (a date, version, "2k tokens",
"lines 2-4") no longer passes. Verified by 16 adversarial cases locked into
`tests/test_check_token_discipline.sh` (all green). Two adversarial passes proved
fully-robust NL detection is not regex-achievable; the residual classes are
documented in the checker comment and tracked in `08-loop-bound-residuals.md`.
On the real tree this surfaced 5 previously-masked `drain/reference.md` relaunch
paragraphs (2 genuine no-adjacent-bound cases for the task-03 retrofit to
cross-reference `max-generations cap of 10`; 3 are `is_live_loop` over-firing on
descriptive/heading prose — a separate concern, not this task).
