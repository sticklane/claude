Status: done
Discovered-from: specs/agentprof-skill-audit/tasks/03-outcome-classification.md
Spec: ../SPEC.md
Blocking: no
Touch: agentprof/internal/judge/fake.go, agentprof/internal/judge/cli_test.go

# judge.Fake needs a per-call-sequenced Replies mode

The shared `internal/judge.Fake` supports only a single fixed `Reply`, so
task 03's 3-call generic-rubric aggregation tests needed a locally-scripted
judge instead. Task 04 (CLI wiring) will likely hit the same need; a
`Replies []string` mode on `judge.Fake` would let both tasks share one
fake implementation instead of each writing its own.

## Acceptance

- [x] `judge.Fake` gains a `Replies []string` field; a non-empty `Replies`
      drives per-call-sequenced replies (Nth call returns `Replies[N]`),
      falling back to the single `Reply` field once exhausted, with an empty
      `Replies` leaving the original single-`Reply` behavior unchanged.
      Implemented in `agentprof/internal/judge/fake.go`.
- [x] `cd agentprof && go test ./internal/judge/ -run TestFake` passes
      (red-first): `TestFakeReturnsRepliesInSequence` (three calls return the
      three replies in order, all recorded in `Calls`) and
      `TestFakeRepliesFallBackToReplyWhenExhausted` (post-exhaustion call
      returns `Reply`). Red confirmed via compile failure on the missing
      `Replies` field before implementation.
- [x] `bash agentprof/scripts/check.sh` green (format-check, vet, tests) —
      the additive field is backward-compatible; no existing test regressed.

## Decisions

- Exhaustion falls back to the existing `Reply` field (defaults to `""`),
  not a hardcoded `"unknown"` — this keeps the mode generic across judges
  and preserves the single-`Reply` behavior when `Replies` is empty.
  Task 03's local `scriptedOutcomeJudge` used an outcome-specific `"unknown"`
  default; consuming tests that want that supply `Reply: "unknown"`.
- Scope kept to adding the mode. Refactoring tasks 03/04's already-merged
  local scripted fakes onto this shared mode is out of this task's Touch;
  the capability now exists for future consumers.
