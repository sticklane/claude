# Verification: 01-fast-forward-tolerant-assert

Verdict: PASS

## Reproduction command

```
ASSERT=/Users/sjaconette/claude/.claude/worktrees/agent-a6b0aca0d82065802/evals/drain/01-rolling-window/assert.sh \
  bash /private/tmp/claude-501/-Users-sjaconette-claude/eed20d5f-829c-4a98-94ea-1e780af8aede/scratchpad/build_fixtures.sh \
  /private/tmp/claude-501/-Users-sjaconette-claude/eed20d5f-829c-4a98-94ea-1e780af8aede/scratchpad/verify-fixtures
```

## Per-criterion results (actual output)

- Fixture A (task01 fast-forward, task02 real merge) — expected PASS exit 0.
  Actual: `assert: all checks passed (2 tasks done, 2 rolling-window
  landings, per-task Touch enforced)`, exit 0. **PASS**
- Fixture B (both real merges, no-regression control) — expected PASS exit 0.
  Actual: `assert: all checks passed (2 tasks done, 2 rolling-window
  landings, per-task Touch enforced)`, exit 0. **PASS**
- Fixture C (fast-forward done-flip commit itself touches out-of-Touch
  `src/gamma.sh`) — expected FAIL naming the violation.
  Actual: `ASSERT FAIL: task 01 landing changed src/gamma.sh, outside its
  Touch [src/alpha.sh]`, exit 1. **PASS**
- Fixture C' (fast-forward across two commits; earlier commit touches
  `src/gamma.sh`, done-flip commit clean) — expected FAIL naming the
  violation from the earlier commit (proves full-range diff, not
  done-flip-only).
  Actual: `ASSERT FAIL: task 01 landing changed src/gamma.sh, outside its
  Touch [src/alpha.sh]`, exit 1 — identical failure fires even though the
  violation is in the earlier, non-done-flip commit, confirming the range
  diff. **PASS**
- Fixture D (one fast-forward commit flips both tasks' Status — barrier) —
  expected FAIL barrier check.
  Actual: `ASSERT FAIL: landing 75ccff77c96e64912d22e324b68bbf4c1b6e3cd7
  flips 2 task files at once (all-in-one barrier, not a rolling-window
  landing)`, exit 1. **PASS**
- Fixture E (both tasks fast-forward, zero merge commits anywhere) —
  expected PASS exit 0 (no hidden merge-count floor).
  Actual: `assert: all checks passed (2 tasks done, 2 rolling-window
  landings, per-task Touch enforced)`, exit 0. **PASS**

All 6 outputs match the caller-specified expectations exactly, run in a
single session's log (raw output captured above, one `build_fixtures.sh`
invocation).

Additionally confirmed: `assert.sh` no longer contains any
`git rev-list --merges` / merge-count-floor logic (`grep -n "merges\|rev-list"
evals/drain/01-rolling-window/assert.sh` shows only the unrelated
`--max-parents=0` root lookup, the `--first-parent --topo-order` walk, and a
`--parents` parent count — no `--merges`), consistent with fixture E passing
for the right reason rather than a residual floor happening not to trip.

## Evidence-doc update

`git diff a1945eab8dceacc1ad38bafbb4d21cb2f4c71109 -- specs/drain-rolling-window/evidence/06-drain-eval-scenario.md`
shows a new appended section "Fast-forward-tolerant landing identification
(spec drain-eval-merge-commit-assertion, 2026-07-07)" that: explains the new
done-flip-anchored mechanism, replaces the stale "2 merge commits" framing,
and includes a fixture table (A/B/C/C'/D/E) whose "Result" column matches
this verification's independently reproduced output verbatim (e.g. the
`src/gamma.sh` Touch-violation message for both C and C', the barrier
message for D). No existing content in the file was removed or altered —
the change is a pure append. **PASS**

## Task-file append-only check

```
git diff a1945eab8dceacc1ad38bafbb4d21cb2f4c71109 -- '*/tasks/*.md'
```
Only one task file changed
(`specs/drain-eval-merge-commit-assertion/tasks/01-fast-forward-tolerant-assert.md`),
and the diff is a pure insertion of a `<!-- PLAN (build, task 01): ... -->`
comment block after the header fields — 23 lines added, 0 removed. Goal,
Touch, Steps, and Acceptance sections are byte-identical to the base
version. **PASS (append-only)**

Note: unlike the append-only rule's example set (Status flip / checkbox
ticks / evidence-citation lines), this diff contains none of those —
`Status:` is still `in-progress` and all Acceptance checkboxes are still
unticked in the working tree. This is not a violation of the append-only
constraint (nothing disallowed was added), but it does mean the task file
itself does not yet self-report completion; that determination is made by
this verification pass instead.

## Touch-list / scope-creep check

```
git diff a1945eab8dceacc1ad38bafbb4d21cb2f4c71109 --name-only
```
Output: `evals/drain/01-rolling-window/assert.sh`,
`specs/drain-eval-merge-commit-assertion/tasks/01-fast-forward-tolerant-assert.md`,
`specs/drain-rolling-window/evidence/06-drain-eval-scenario.md`. The first
two of the task's declared `Touch:` list are both present; the task file
itself is the standard self-file exception. No file outside the Touch list
was modified (confirmed via `git status --porcelain` in the worktree, which
lists exactly these three paths and nothing else — no untracked files).
This evidence report (`specs/drain-eval-merge-commit-assertion/evidence/01-fast-forward-tolerant-assert.md`)
is newly added by this verification pass, outside the diff base above.
**PASS (no scope creep)**

## Gates

No `scripts/check.sh` exists in this repo (`ls scripts/check.sh` →
"No such file or directory"). This repo's own gate for the four ultra-path
skills (`evals/lint-ultra-gate.sh`) does not apply — `assert.sh` is an eval
fixture script, not one of critique/drain/build/idea. No applicable gate
was skipped.

## Overfitting check

The rewritten `assert.sh` derives landing ranges generically from each task
file's `Status:` done-flip and the declared `Touch:` list read from the task
file itself — it does not special-case `src/gamma.sh`, `src/alpha.sh`, task
numbers 01/02, or any fixture-specific string. The Touch-violation and
barrier failure messages are parameterized (`task $nn`, `$sha`, the actual
changed path), not hardcoded to the fixture's exact inputs. No indication
of overfitting to the specific fixture shapes.

## Verdict

**PASS** — all 6 fixture criteria (A, B, C, C', D, E) reproduce the exact
caller-specified pass/fail outcomes; the evidence doc was correctly updated
per step 5; the task-file diff is append-only (plan comment block only, no
Goal/Steps/Touch/Acceptance rewrites); and the working tree touches only
the declared Touch-list files plus this new evidence report.
