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
- Subject length: target ≤72 characters, hard cap 100. The subject is a
  scannable one-line summary — when the length rule bites, move detail into
  the body, never abbreviate to the point of losing meaning.
- Subject/body split: the subject states _what changed_; everything else —
  ratification notes, verifier evidence, audit notes, acceptance detail,
  multi-clause context — belongs in the body, after a blank line. A commit
  needing more than the subject affords gets a body, not a longer subject.
- Sanctioned orchestration prefixes: alongside the conventional types
  above, machinery commits use `drain:`, `merge:`, `spec:`, and
  `breakdown:` as their `<type>`. These name the pipeline stage that
  authored the commit rather than a code-change category.
- Machinery-contract subjects are regex-pinned — do not reword them to
  satisfy the length rule. `drain: <spec-slug> task NN in-progress`
  (singular "task") is the canonical case: drain's diff-base recovery greps
  for that exact shape (`.claude/skills/drain/SKILL.md`), so an agent must
  reproduce it verbatim even when a longer slug pushes the subject past the
  ≤72 target — the hard cap 100 and the contract shape both hold, the soft
  target yields.
- Agent-authored commits keep the harness-provided `Co-Authored-By` trailer;
  never strip it.

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
