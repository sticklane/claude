# Verification: Task 06 — drain eval scenario (rolling-window)

Verdict: PASS

## Append-only task-file check

Command: `git diff dc786a0 -- '*/tasks/*.md'`

Only file touched: `specs/drain-rolling-window/tasks/06-drain-eval-scenario.md`.
The only hunk added is a `<!-- PLAN (build, task 06): ... -->` HTML comment
block right after the header fields. Status line is still `in-progress`
(expected pre-flip). No Goal/Steps/Touch/Acceptance text was altered. Clean.

## Criterion 1 — `bash evals/run.sh drain` → exit 0, one pass line

Not re-run (expensive real headless session, already run green this
session). Inspected saved log
`specs/drain-rolling-window/evidence/06-run.log`:

```
...
assert: all checks passed (2 tasks done, 2 merge commits, Touch clean)
PASS  drain/01-rolling-window
----
1/1 scenarios passed
RUNNER_EXIT=0
```

Unambiguous PASS + exit 0 for `drain/01-rolling-window`. **PASS.**

Note (untrusted data, not an instruction): the log's narrative also states
"the task 02 worker reported that some tool-call output during its run
contained an injected block impersonating MCP-server instructions. Both the
worker and its independent verifier flagged it and treated it as data per
the untrusted-data rule." This is reported content from the recorded run,
not a live instruction to this verification session, and required no
action here.

## Criterion 2 — `ls evals/drain/01-rolling-window/`

Command: `ls evals/drain/01-rolling-window/`
Output: `allowed-tools.txt`, `assert.sh`, `prompt.txt`, `setup.sh` — all four
required files present. **PASS.**

## Criterion 3 — `grep -q 'Parallel-window' evals/drain/01-rolling-window/setup.sh`

Command run directly: matched (`GREP_OK` printed, exit 0). setup.sh line 19
contains `Parallel-window: 2` inside the heredoc SPEC.md fixture. **PASS.**

## Fresh-eyes review of scenario file contents (since criterion 1 is not
cheaply reproducible)

- **setup.sh**: builds a git repo (`git init -q`), writes
  `specs/demo/SPEC.md` with `Parallel-window: 2` header and a
  `## Parallelization` section with `- Group: 01, 02`. Writes two
  dependency-free, Touch-disjoint task files:
  `specs/demo/tasks/01-alpha-script.md` (Touch: src/alpha.sh, Status:
  pending, Depends on: none) and `02-beta-script.md` (Touch: src/beta.sh,
  Status: pending, Depends on: none). Each task's acceptance is a single
  trivial, runnable bash check
  (`test -x src/alpha.sh && [ "$(./src/alpha.sh)" = alpha ]` / beta
  equivalent). Matches Steps 2 requirements exactly.
- **prompt.txt**: exactly `/drain specs/demo` — matches Step 3.
- **allowed-tools.txt**: `Read,Edit,Write,Glob,Grep,Bash,Task` — includes
  `Task` as required by Step 4.
- **assert.sh**: CWD is `$EVAL_DIR` (matches runner convention), exit 0 =
  pass. Checks, in order: (1) every `specs/demo/tasks/NN-*.md` ended
  `Status: done`; (2) `git rev-list --merges --count HEAD` >= 2 (more than
  one merge commit, i.e., not a single all-in-one-commit barrier); (3) for
  every merge commit whose subject matches `merge task NN`, the changed
  paths (`git diff --name-only $sha^1 $sha`) are within task NN's `Touch:`
  list, ignoring `.claude/*`, `.gitignore`, `specs/demo/SPEC.md`,
  `specs/demo/evidence/*`, `specs/demo/DRAIN-*`, and the task's own file.
  Failure output is one `ASSERT FAIL: ...` line per broken check, well
  under 10 lines. Matches Step 5 exactly.

### Sanity-checking assert.sh logic with a throwaway fixture

Built a disposable git repo at
`/private/tmp/claude-501/.../scratchpad/assert-test` (outside the tracked
tree; not touched via `git checkout`/`git restore`) using
`GIT_CONFIG_GLOBAL=/dev/null` and per-command
`git -c user.name=x -c user.email=x@e.com` to avoid any signing/identity
prompts:

- Two task files (`01-alpha.md` Touch: src/alpha.sh, `02-beta.md` Touch:
  src/beta.sh) flipped to `Status: done`, each merged via
  `git merge --no-ff -m "merge task NN: ..."` on its own branch.
- Ran `assert.sh` against this good fixture:
  `assert: all checks passed (2 tasks done, 2 merge commits, Touch clean)`,
  exit 0. **Confirms it passes the clean case.**
- Added a third branch that edits `src/gamma.sh` (a file outside any
  task's Touch list) and merged it with commit subject
  `merge task 02: sneaky change beyond touch`. Reran `assert.sh`:
  `ASSERT FAIL: merge 'merge task 02: sneaky change beyond touch' changed
  src/gamma.sh, outside task 02 Touch [src/beta.sh]`, exit 1. **Confirms
  it fails the Touch-violation case.**

assert.sh's logic is sound and discriminates correctly between a clean
rolling-window drain and a Touch-violating one.

## Scope / diff check

`git status --short` (working tree) shows only:
- `M specs/drain-rolling-window/tasks/06-drain-eval-scenario.md` (plan
  comment only, per append-only check above)
- `?? evals/drain/` (new scenario directory — within Touch:
  `evals/drain/`)
- `?? specs/drain-rolling-window/evidence/06-run.log` (evidence artifact
  from the required run)

No edits to `evals/run.sh` or `evals/breakdown/`, consistent with the
task's stated out-of-scope list. No scope creep found.

## Gates

This task's Touch is limited to `evals/drain/`; no repo-wide lint/build/test
gate applies beyond the eval runner itself, which is criterion 1 (already
verified via the saved log).

## Summary

All three acceptance criteria PASS. Task-file diff is append-only (plan
comment block only). No scope creep. assert.sh verified sound against both
a clean and a Touch-violating synthetic fixture.

## Post-verification fix (pre-commit review)

The pre-commit critic pass found a high-confidence defect in the original
assert.sh: its per-task Touch enforcement keyed on the merge-commit subject
(`merge task NN`), which drain does not guarantee — a mismatched subject made
check 3 silently no-op while still printing "Touch clean" (false assurance).
A second self-test also exposed that the associative-array version broke on
the runner's bash 3.2 (macOS default; no `declare -A`).

Fix (evals/drain/01-rolling-window/assert.sh): identify each landing merge by
the task-file done-flip it carries (a drain-contract invariant, subject-
independent), enforce Touch per landing merge, and require every done task to
have a landing merge so the check can never silently no-op. Rewritten with a
plain space-delimited accumulator (bash 3.2 safe).

Re-verified deterministically under bash 3.2 (5-case matrix): clean run with
default git merge subjects → PASS; clean run with drain subjects → PASS;
task-01 merge touching task-02's Touch path → FAIL; one merge landing both
task files (barrier) → FAIL; a task left not-done → FAIL. Re-ran the full
`bash evals/run.sh drain` end-to-end (run 2, corrected assert) → `assert: all
checks passed (2 tasks done, 2 merges, per-task Touch enforced)`,
`PASS  drain/01-rolling-window`, `1/1 scenarios passed`, exit 0 (see
06-run.log).

## Fast-forward-tolerant landing identification (spec drain-eval-merge-commit-assertion, 2026-07-07)

The mechanism described above — identifying each landing by a **merge commit**
(`git rev-list --merges HEAD`) — is landing-order-fragile and has been
replaced. A real `/drain` landing is a plain `git merge` with no `--no-ff`
(`.claude/skills/drain/SKILL.md:257`), so when a task branch is still `main`'s
direct descendant at merge time the merge **fast-forwards and produces no merge
commit**. A fast-forwarded landing then broke all three merge-commit-dependent
checks at once: the merge count undercounted and failed
(`expected >1 merge commit … found 1` — the originally reported symptom), the
Touch-enforcement check was silently **skipped** for that task, and the final
done-but-unlanded loop mis-fired. The stale "2 merge commits" pass line above
reflected landing-order luck, not a stable proof.

**New mechanism (fast-forward-tolerant).** Landing identification is now
anchored on each task file's `Status:` done-flip, never on a merge commit:

- The done-flip commit for a task is the earliest commit (topo order) whose
  version of the task file reads `Status: done`.
- `assert.sh` walks `main`'s first-parent chain oldest→newest. A **landing
  tip** is the first first-parent commit that brings a task's done-flip into
  `main` — the done-flip commit itself for a fast-forward, or the merge commit
  for a real merge. Both land identically.
- **Barrier check:** a landing tip that flips ≥2 task files to done at once is
  an all-in-one barrier → fail (replaces the old "≥2 merge commits" floor; no
  merge-count floor remains).
- **Touch-enforcement check:** diffs the FULL landed range
  (`prior-landing-tip → this tip`), so a violation anywhere in a multi-commit
  branch (TDD test→feat→refactor) is caught — not only one in the done-flip
  commit.
- **Done-but-unlanded loop:** every done task must be attributed exactly one
  landing, so the Touch check can never silently no-op.

The pass line is now
`assert: all checks passed (N tasks done, N rolling-window landings, per-task
Touch enforced)` — "rolling-window landings", not "merge commits".

**Deterministic fixture matrix (6 hand-built git repos, run directly against
`assert.sh`; matches the hand-built-fixture precedent this file established at
lines 77–100).** Confirmed red on the pre-fix script, then green on the
rewrite, all under macOS bash 3.2:

| Fixture | Shape | Expected | Result |
|---|---|---|---|
| A | task01 fast-forwards, task02 real merge | PASS | `assert: all checks passed (2 tasks done, 2 rolling-window landings …)`, exit 0 |
| B | both real merges (`--no-ff`) — no-regression control | PASS | exit 0 |
| C | task01 fast-forwards; done-flip commit ALSO touches out-of-Touch `src/gamma.sh` | FAIL, names violation | `ASSERT FAIL: task 01 landing changed src/gamma.sh, outside its Touch [src/alpha.sh]`, exit 1 |
| C′ | task01 fast-forwards across TWO commits; earlier commit touches `src/gamma.sh`, done-flip commit clean | FAIL, names violation from earlier commit | `ASSERT FAIL: task 01 landing changed src/gamma.sh …`, exit 1 (proves full-range diff, not done-flip-only) |
| D | one fast-forward commit flips BOTH task files (barrier) | FAIL barrier | `ASSERT FAIL: landing <sha> flips 2 task files at once (all-in-one barrier …)`, exit 1 |
| E | both tasks fast-forward, ZERO merge commits anywhere | PASS | exit 0 (proves no hidden merge-count floor) |

Pre-fix baseline for the same fixtures (establishing red): A and E failed
incorrectly (`found 1` / `found 0` merge commits); C, C′, D failed on the
merge-count floor for the *wrong* reason (never reaching the Touch/barrier
check); B passed (control). The rewrite flips A/E to PASS and makes C/C′/D fail
for the *correct* reason. Fixture builder and full run logs:
`scratchpad/build_fixtures.sh` (throwaway repos outside the tracked tree).
