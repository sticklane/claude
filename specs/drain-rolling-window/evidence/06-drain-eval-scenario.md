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

## Fast-forward-tolerant landing identification (spec drain-eval-merge-commit-assertion)

The fix above still identified a landing by its **merge commit**
(`git rev-list --merges HEAD`). A 2026-07-06 runtime sweep found that
landing-order-fragile: when a task branch is still `main`'s direct
descendant at merge time, `git merge` fast-forwards silently and produces
**no** merge commit — so the merge-count check under-counts and fails, the
done-but-unlanded loop reports the task unlanded, and the Touch check for
that task is silently **skipped**. Production `/drain` does not force
`--no-ff` (`.claude/skills/drain/SKILL.md`), so the eval must tolerate
fast-forwards rather than the eval demanding merge commits production
doesn't produce.

`assert.sh` now identifies each task's landing by its `Status:` **done-flip
commit** — the earliest commit reachable from `HEAD` whose blob reads
`Status: done` — which exists whether the landing fast-forwarded or merged.
That one mechanism feeds all three previously merge-dependent checks:

- **Rolling-window / barrier check**: counts distinct done-flip landings and
  fails if a single commit is the done-flip for ≥2 task files (an
  all-in-one barrier). No `git rev-list --merges` floor remains, so a
  history with zero merge commits still passes.
- **Touch-enforcement check**: diffs the **full landed range**
  `fork-point..done-flip` (fork-point = the closest other-task done-flip
  that is an ancestor of this landing, else the repo root/base commit) — not
  just the done-flip commit — so a violation in any branch commit is caught,
  not only one in the commit that happens to flip `Status:`.
- **Done-but-unlanded loop**: a task is landed iff a done-flip commit exists
  in `HEAD`'s history; a done task with none fails loudly (the check can
  still never silently no-op).

Verified deterministically via six hand-built git fixtures (per this repo's
own synthetic-fixture precedent, above), run directly against `assert.sh` in
one session — results below (not a full `/drain` re-run, which cannot be
forced to exhibit fast-forward-vs-merge on demand):

- **Fixture A** — task 01 fast-forwards, task 02 real merge → PASS
  (`assert: all checks passed (2 tasks done, 2 distinct landings, per-task
Touch enforced)`, exit 0). This is the exact reported-bug shape; the old
  script failed it with `expected >1 merge commit ... found 1`.
- **Fixture B** — both tasks land via `git merge --no-ff` (real merges) →
  PASS, exit 0 (no regression for the original design case).
- **Fixture C** — task 01 fast-forwards and its done-flip commit itself also
  creates `src/gamma.sh` (outside its Touch) → FAIL, exit 1:
  `task 01 landing changed src/gamma.sh, outside its Touch [src/alpha.sh]`.
  Proves the Touch check runs (not silently skipped) on a fast-forwarded
  landing.
- **Fixture C'** — task 01 fast-forwards across two commits: an earlier
  commit adds `src/gamma.sh`, a separate later commit only flips `Status:`
  to done → FAIL, exit 1, naming `src/gamma.sh`. Proves the Touch check
  diffs the full fork-point..done-flip range, not just the done-flip commit.
- **Fixture D** — one fast-forward commit flips both task files' `Status:`
  at once (a barrier) → FAIL, exit 1:
  `commit <sha> flips task 01 and task 02 at once (all-in-one barrier)`.
  Barrier detection survives the rewrite and works with zero merge commits.
- **Fixture E** — both tasks fast-forward, **zero merge commits anywhere**
  in history → PASS, exit 0. Proves no hidden merge-count floor remains.

Fixtures A and E are the cases the old merge-commit-based script failed
incorrectly; C/C'/D previously failed only by accident of the merge-count
check firing first, and now fail for the correct reason. The stale "2 merge
commits" success line is replaced by "N distinct landings" — landings, not
merges, are what the rolling-window contract actually requires.
