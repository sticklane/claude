# Task 07: constrain loop-bound numeral position in bin/check-token-discipline

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: draft
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
