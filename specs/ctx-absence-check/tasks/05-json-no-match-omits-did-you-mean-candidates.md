Status: pending
Discovered-from: spec-completion review (2026-07-21)
Spec: ../SPEC.md
Blocking: no

# JSON no-match output omits the "did you mean" candidates text mode emits

Text-mode `sig`/`refs` no-match prints near-miss candidates before the
boundary note (task 02), but the `--json`/MCP no-match object carries
only `boundary_note` + `suggested_check`, not the candidate list — a JSON
consumer has no way to surface the same R4 suggestion. This may be an
intentional text-mode-only scoping of R4 (task 02's own JSON tests assert
only the two existing keys, not a new candidates key), or an unintended
parity gap. Left unfixed by the reviewing worker pending a decision on
whether JSON parity was intended.

## Acceptance

<!-- draft: needs runnable criteria before promotion. Likely shape: either
(a) confirm text-only scoping is intentional and close this as obsolete,
or (b) add a `did_you_mean` JSON key mirroring the text-mode candidate
list, with a test asserting it appears when candidates exist and is
absent/empty when none do. -->
