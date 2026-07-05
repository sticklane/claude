# Quality discipline

Practices that hold for any code change, attended or unattended. The gate
skill enforces the check layer mechanically; /build encodes the worker
procedure — this rule states the discipline both assume.

## TDD — red, green, refactor

- **Red**: write a failing test first and run it — confirm it fails for the
  right reason. A test that passes immediately isn't testing anything new.
- **Green**: write the minimal code that makes it pass; no extra features
  "just in case".
- **Refactor**: improve structure with tests green; never change behavior
  and tests in the same step.
- Bug fixes start with a failing reproduction; refactors start with a
  safety-net test.

## Test rules of thumb

- Test behavior, not implementation — assert what it does, never internals
  or exact output strings (parse, then assert structure).
- One behavior per test; fresh objects per test; any execution order.
- Mock only slow/external dependencies — over-mocking tests nothing real.
- Every test asserts something; "runs without error" is not a test.
- Names describe scenario and expectation:
  `test_detector_returns_none_when_no_ball_in_frame`.

## Commits

- Small, focused, atomic: commit at each TDD step (test → feat → refactor)
  and when a task completes; never leave finished work uncommitted.
- Format: `<type>: <subject>` — feat, fix, test, refactor, docs, style,
  perf, chore.
- Never commit: debugging prints, commented-out code, broken tests, or
  mixed unrelated changes (split them).

## Checks

Run the repo's canonical check green before calling work done. Repos with
gates installed enforce this mechanically (two layers: fast staged-file
pre-commit + full check in the Stop hook) — the gate skill owns the
mechanism; don't hand-write formatting or lint reminders into workflows.
