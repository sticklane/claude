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
- **Rigor-scoped.** This TDD mandate binds `Rigor: production` work (absent
  = production); a `Rigor: prototype` spec substitutes a mechanical
  acceptance-command run for red-first per the rigor-tier mechanism
  (specs/rigor-tier — cited, not restated), surfaced in `/list-specs`'s
  table.

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

## Documentation currency

Scoped to `/build`'s attended completion step — not to "any code change,
attended or unattended" the way this file's opening line otherwise frames
it. A human is present at `/build` to judge documented-state relevance;
`/drain`'s unattended workers are out of scope. Before `/build` finishes a
task, check whether the diff invalidates what `AGENTS.md`'s Map (a
new/moved/removed top-level component), Commands (a documented command's
behavior or invocation changed), or State sections claim, or anything
README.md tells an end user — if so, update it in the same commit, not a
follow-up task. This is a discipline reminder, not a mechanical gate: no
automated check diffs AGENTS.md's prose against the codebase. It complements
rather than replaces a task's own `Touch:` header and acceptance criteria
scoping doc updates — a safety net for what that decentralized pattern
misses, applying regardless of whether the task author thought to add
`AGENTS.md`/README to `Touch:`.
