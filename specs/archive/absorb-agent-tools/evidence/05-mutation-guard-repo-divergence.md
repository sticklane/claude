# Verification: 05-mutation-guard-repo-divergence

Verdict: PASS (with process findings — see below)

## Criterion 1 — full suite passes
Command: `cd agent-console && python3 -m pytest tests/test_parsers.py -v`
Result: `24 passed in 1.21s`. Includes the two new tests:
- `TestTrackedReposUnionsDefaultRoots::test_default_roots_only_repo_is_tracked` PASSED
- `TestTrackedReposUnionsDefaultRoots::test_default_roots_only_repo_accepted_by_start_agent` PASSED
Status: ✓ PASS

## Criterion 2 — default_roots-only repo accepted by `_tracked_repo_reals()`
Verified via the two tests above (not by inspection): both patch `parse_repos`
to return `[]` and `workboard.default_roots` to return a temp root containing
only a `.git`-marked repo dir absent from any REPOS.md, then call the real
`_tracked_repo_reals()` / `start_agent()`. Both assert the repo is accepted
(`assertIn(realpath, reals)`, `assertTrue(ok, msg)`), and both PASSED.
Status: ✓ PASS

## Criterion 3 — `_tracked_repo_reals()` reads both sources
Command: `grep -n 'def _tracked_repo_reals' agent-console/agent-console.py`
Output: `1405:def _tracked_repo_reals() -> set[str]:`
Body (lines 1405-1420) unions `parse_repos()` with
`workboard.find_repos(workboard.default_roots(), max_depth=3)` inside a
`try/except Exception: pass` (fail-soft on a broken walk).
Status: ✓ PASS

## Additional required checks
(a) `test_start_rejects_untracked_cwd` — ran in the same pytest invocation
above: PASSED. The guard still rejects genuinely untracked paths.

(b) `parse_repos()` unchanged — `git diff -U0 538548b -- agent-console/agent-console.py`
shows no hunk touching `def parse_repos` (lines 369-386 identical to base).
Confirmed by direct read of the function body as well. ✓ unchanged.

(c) Task-file append-only check — `git diff 538548b -- specs/absorb-agent-tools/tasks/05-mutation-guard-repo-divergence.md`
produced **no output** (file is byte-identical to base). No violation of the
append-only rule, but this means Status is still `in-progress` and all three
acceptance checkboxes are still unchecked in the task file despite the fix
existing and its tests passing — the task file has not been updated to
reflect the (apparently working) state of the code.

## Findings (not criteria failures, but should be reported)

1. **Uncommitted implementation.** The actual `_tracked_repo_reals()` fix in
   `agent-console/agent-console.py` is uncommitted working-tree state (`git
   status` shows it modified, not staged/committed). Only the regression
   test (commit `5acd5b3`) is committed. This violates the repo's own
   commit discipline ("never leave finished work uncommitted"; commit at
   each TDD step) — red (test, committed) is done but green (fix) never
   landed a commit.
2. **Scope creep / formatting drift outside Touch intent.** The uncommitted
   diff to `agent-console.py` also reformats two unrelated blocks that have
   nothing to do with this task's fix:
   - `_adapt_board(...)` signature collapsed from a 3-line wrap to one line
     (line ~578).
   - Two f-strings in `render_workboard` changed from single- to
     double-quoted delimiters with inner quotes flipped (lines ~1247-1249).
   These are not required by Step 1 ("union at the call site only") and are
   not part of the regression test. `agent-console.py` is in the task's
   `Touch:` list, so the file itself is in scope, but these specific hunks
   are unrelated formatting churn, not the described fix — flag as
   scope creep for the closing reviewer to squash out or justify.
   Similarly, the committed test file (`5acd5b3`) reflows several
   pre-existing tests' dict literals to one-key-per-line — plausibly an
   auto-formatter (black/ruff) run as part of a commit hook rather than an
   intentional edit; harmless but also not required by Step 2.

## Gates
No repo-level `scripts/check.sh` found under `agent-console/`; pytest is the
project's own test command and was run directly per criterion 1.

## Summary
All three literal acceptance criteria pass when exercised. The regression
test genuinely exercises the union behavior (not a tautology): it mocks the
two data sources independently and calls the real guard + real
`start_agent`. `parse_repos()` is untouched. The task file itself was not
edited (no append-only violation) but also was not updated to reflect
completion — Status/checkboxes still say in-progress/unchecked. The
uncommitted fix and unrelated formatting hunks are process/scope findings,
not acceptance failures.
