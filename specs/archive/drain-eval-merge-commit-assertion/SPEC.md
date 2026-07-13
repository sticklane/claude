# Fix landing-order-fragile assertion in the drain rolling-window eval

## Problem

`evals/drain/01-rolling-window/assert.sh` identifies every task's landing
by looking for a merge commit (`git rev-list --merges HEAD`). This is
landing-order-fragile: when a task's branch happens to still be `main`'s
direct descendant at merge time, `git merge` fast-forwards silently and
produces **no** merge commit. Because landing identification is shared
infrastructure inside `assert.sh`, a fast-forwarded landing doesn't just
break one check — it breaks three:
- the merge-count check (`>= 2`) undercounts and fails — the originally
  reported symptom;
- the final per-task loop, which also derives `landed` from
  `git rev-list --merges`, hits `fail "task $nn ended done but no merge
  introduced its landing"` for that task;
- the Touch-enforcement check for that same task is silently **skipped**
  (not failed — skipped), which is exactly the kind of silent no-op that
  check exists to prevent.

Found during a runtime verification sweep (2026-07-06) by actually running
the eval scenario end-to-end (a real ~25-minute headless `/drain
specs/demo` session, not a re-inspection of a saved log): the run failed
with `ASSERT FAIL: expected >1 merge commit (rolling window), found 1`, even
though inspecting the kept fixture's `git log` confirmed both tasks landed
correctly — one merged normally (producing a merge commit), the other
fast-forwarded (producing none). The task's own evidence file records "PASS
on both attempts," which was landing-order luck, not a stable proof — this
is exactly the kind of flaky-gate problem the /verify skill exists to
catch, and it's now caught.

**Already resolved by checking the source (no further investigation
needed):** real, non-eval `/drain` runs do NOT force `--no-ff` either —
`.claude/skills/drain/SKILL.md:257` just says "Then merge the task branch,"
a plain merge with no `--no-ff` flag anywhere in `SKILL.md` or
`reference.md`. So forcing `--no-ff` only in the eval (option (a) from an
earlier draft of this spec) would make the eval stricter than production
behavior, which R2 explicitly forbids. The fix is to make `assert.sh`'s
landing identification itself tolerant of fast-forwards — not to change
merge behavior anywhere.

## Solution

Rewrite `assert.sh`'s landing-identification mechanism so it doesn't rely
on merge commits existing at all. Identify a task's landing by something
that's true regardless of fast-forward vs. real merge — e.g. each task
file's `Status:` flipping to `done` on `main` (matched against the task's
own branch/commit history), or the presence of the task's landing commit
itself (fast-forwarded or not) in `main`'s history. Whatever mechanism is
chosen, it must feed **all three** checks that currently depend on merge
commits (merge-count, Touch-enforcement, and the final done-but-unlanded
loop) — not just patch the merge-count assertion in isolation and leave
the other two still merge-commit-dependent.

## Requirements

R1: `assert.sh`'s landing identification (used by the merge-count check —
including its barrier-vs-rolling-window distinction, which currently
assumes one task per merge commit — the Touch-enforcement check, and the
final "task ended done but unlanded" loop) works correctly for both
fast-forwarded and true-merge landings. In particular: the Touch-enforcement
check must still actually run and correctly fail on a Touch violation in a
fast-forwarded landing — not silently skip it, which is the exact defect
this spec exists to close (see fixture C below).

The Touch-enforcement check must diff the FULL landed range for a task —
from the point its branch forked off `main` (or the prior task's landing,
whichever is later) through its done-flip commit — not just the done-flip
commit in isolation. Real drain branches are typically multi-commit
(TDD: test → feat → refactor), so a Touch violation can live in any commit
of the branch, not only the one that happens to flip `Status:` to `done`.
Diffing only the done-flip commit would silently miss violations in earlier
commits of the same landing — a relocated version of the exact silent-skip
bug this spec exists to close. (See fixture C', below, which specifically
guards this.)

R2: `assert.sh`'s fixed behavior matches real `/drain` production behavior
— confirmed above that production does not force `--no-ff`
(`.claude/skills/drain/SKILL.md:257`), so the fix must not require
production to change; it only changes what the eval script detects.

R3: The fix is verified primarily via cheap, deterministic hand-built git
fixtures run directly against `assert.sh` — not via a full, non-deterministic
`/drain` re-run. (`specs/drain-rolling-window/evidence/06-drain-eval-scenario.md:82-95`
already shows this repo's own precedent: a synthetic git repo built by hand
and run straight through `assert.sh`, and `evals/runner-selftest.sh`
establishes the same pattern for the eval runner itself.) One optional full
`/drain` scenario run (~25 min) may be used as a final smoke check, but it
is not the primary acceptance gate, since fast-forward-vs-merge is an
emergent property of concurrent worker timing that a live run cannot be
made to reliably exhibit on demand.

## Out of scope

- Any other eval scenario beyond `drain/01-rolling-window` — this spec is
  scoped to the one confirmed-flaky assertion mechanism.
- Broader refactoring of the eval runner (`evals/run.sh`) itself.
- Changing drain's actual merge behavior in production (`SKILL.md`/
  `reference.md`) — confirmed unnecessary; see Problem section.

## Acceptance criteria

- [ ] Hand-built fixture A: a synthetic git repo where task 01's landing
      fast-forwards (`git merge` with no `--no-ff`, branch still main's
      direct descendant) and task 02's landing produces a real merge
      commit — `bash evals/drain/01-rolling-window/assert.sh` (run directly
      against this fixture, not via a full `/drain` session) passes: merge
      count check, Touch-enforcement check, and the done-but-unlanded loop
      all correctly recognize task 01's fast-forwarded landing.
- [ ] Hand-built fixture B: both task 01 and task 02 land via real merge
      commits (`git merge --no-ff` for both, matching the original
      evidence file's fixture-construction approach) — `assert.sh` still
      passes, confirming no regression for the case the original assertion
      was designed for.
- [ ] Hand-built fixture C (negative — this is the fixture that actually
      proves the silent-skip bug is fixed, not just that the happy path
      still works): task 01 lands via fast-forward, and the out-of-Touch
      change is committed as part of **that same fast-forward landing
      commit** — i.e. the commit that flips task 01's `Status:` to `done`
      also touches a file outside task 01's declared Touch list. This is
      NOT the same shape as the `src/gamma.sh` example in
      `specs/drain-rolling-window/evidence/06-drain-eval-scenario.md:92-95`
      (that example is a separate, non-landing commit with no `Status:`
      flip — under `assert.sh`'s done-flip-based landing identification,
      a violation in a separate non-landing commit is correctly skipped by
      design, and building fixture C that way would make its own "must
      FAIL" criterion unsatisfiable). The violation must live IN the
      landing commit itself. `assert.sh` **fails** (non-zero exit, naming
      the Touch violation). Fixtures A and B alone are both green-only and
      can't distinguish "the Touch check ran and passed" from "the Touch
      check was silently skipped because the landing fast-forwarded" —
      fixture C is the only construction that proves the skip is actually
      closed.
- [ ] Hand-built fixture C' (diff-range regression — guards the multi-commit
      case R1 calls out): task 01's fast-forwarded branch has TWO commits
      before landing — an earlier commit that touches a file outside task
      01's Touch list, and a later, separate done-flip commit that only
      flips `Status:` to `done` and touches nothing else. `assert.sh`
      **fails**, naming the Touch violation from the earlier commit — this
      is only possible if the Touch check diffs the full landed range
      (fork-point → done-flip), not just the done-flip commit in isolation.
      A same-commit-only implementation (satisfying fixture C alone) would
      incorrectly pass this fixture.
- [ ] Hand-built fixture E (all-fast-forward — the actual worst-case shape
      the original bug report reproduced): task 01 AND task 02 both land
      via separate fast-forward commits, with **zero real merge commits**
      anywhere in the resulting history — `assert.sh` still passes. This
      guards against a rewrite that keeps a hidden residual merge-count
      floor (e.g. `git rev-list --merges --count HEAD >= 1`) which fixtures
      A/B/C/D would not catch, since each of them still contains at least
      one real merge commit somewhere in its history.
- [ ] Hand-built fixture D (barrier-detection regression): one fast-forward
      commit lands two task files at once (an all-in-one-commit "barrier"
      landing, not a genuine rolling-window admission) — `assert.sh` still
      **fails** the barrier check, confirming the landing-identification
      rewrite didn't accidentally make a fast-forwarded barrier
      undetectable (the original barrier check assumed one task per merge
      commit; verify it still holds under the new mechanism).
- [ ] Optional smoke check: one full `bash evals/run.sh drain` end-to-end
      run passes. Not required to reproduce the fast-forward case
      specifically (can't be forced), just confirms the real scenario still
      runs clean end-to-end with the new `assert.sh`.
- [ ] `specs/drain-rolling-window/evidence/06-drain-eval-scenario.md` (the
      correct, full path — this is a different spec slug than this one) is
      updated to reflect the new, fast-forward-tolerant assertion mechanism
      and cites the two hand-built fixture runs above, not the stale "2
      merge commits" claim.

## Open questions

None — resolved above: production doesn't force `--no-ff`
(`.claude/skills/drain/SKILL.md:257`), so the fix is entirely inside
`assert.sh`'s landing-identification logic, verified via deterministic
hand-built fixtures rather than expensive live re-runs.

## Parallelization

Single-track. `tasks/01-fast-forward-tolerant-assert.md` covers R1-R3
end-to-end; no parallel groups.
