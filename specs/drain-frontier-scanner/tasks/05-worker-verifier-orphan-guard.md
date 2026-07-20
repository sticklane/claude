Status: draft
Discovered-from: 02-drain-consumes-scanner.md
Spec: ../SPEC.md
Blocking: no

# Guard against a worker orphaning its own spawned verifier

An `implementation-worker` that spawns its own verifier sub-agent per
build's procedure can have its own turn end (budget/turns exhausted)
before it awaits that child's result — the verifier then notifies the
orchestrator directly once it finishes, bypassing the worker's own
close-out. Observed live in specs/drain-frontier-scanner/tasks/
02-drain-consumes-scanner.md's attempt 2 (2026-07-20): the worker's final
message was a stale "waiting for verifier" line, the task file was left
uncommitted with an unverified "verifier PASS" claim baked into its own
checkbox evidence, and the real verifier's PASS surfaced only via a
delayed task-notification routed to the hub. Drain caught it by
independently re-verifying from scratch rather than trusting either
claim, but nothing structural prevents this — `.claude/rules/
token-discipline.md`'s "a worker that spawns its own verifier awaits it
inline" clause is unenforced. Full narrative in that task's `## Progress`
and `## Discovered` entries.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
