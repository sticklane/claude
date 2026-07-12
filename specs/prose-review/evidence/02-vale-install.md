# Verification: specs/prose-review/tasks/02-vale-install.md

Verdict: PASS

## Per-criterion

1. `bash bin/install-vale && vale --version` → exit 0
   Ran in worktree root. Output:
   ```
   install-vale: done
   exit1=0
   vale version 3.15.1
   exit2=0
   ```
   PASS.

2. `bash bin/install-vale` (second run) → no-op, exit 0
   Captured mtimes of `~/.vale.ini` and `vale/styles/Google` before/after a
   second run:
   ```
   install-vale: done
   exit=0
   --- ini mtime changed? --- UNCHANGED
   --- google dir mtime changed? --- UNCHANGED
   ```
   Confirmed genuinely idempotent (no rewrite, no re-sync), not just exit 0.
   No `brew install` output on this run (vale already on PATH — skip branch
   at bin/install-vale:36 not entered). PASS.

3. `test -f ~/.vale.ini && grep -q '/vale/styles' ~/.vale.ini` → exit 0.
   `~/.vale.ini` StylesPath line:
   `StylesPath = /Users/sjaconette/claude/.claude/worktrees/agent-aa61f06791202f295/vale/styles`
   — absolute path, correctly substituted for this worktree. PASS.

4. `git check-ignore vale/styles/Google >/dev/null` → exit 0.
   `git ls-files vale/ | grep -q accept.txt` → exit 0.
   `git ls-files vale/` output:
   ```
   vale/.vale.ini.template
   vale/styles/config/vocabularies/House/accept.txt
   ```
   `git ls-files vale/styles/Google | wc -l` → 0 (no synced payload tracked).
   PASS.

## Defect sanity-checks

(a) `bin/install-vale`: `STYLES="$REPO/vale/styles"` where
`REPO="$(cd "$(dirname "$0")/.." && pwd)"` — resolves to an absolute path via
`pwd`, substituted into the template with `sed`. Confirmed absolute in the
rendered `~/.vale.ini` (see criterion 3). Clobber guard: writes only if
`$CONFIG` absent, or contents differ AND `--force` given; if it exists and
differs without `--force`, it prints a warning and leaves it untouched
(lines 47-57). Correct.

(b) No Google sync payload under `vale/styles/Google/` is git-tracked
(`git ls-files vale/styles/Google` → empty, `git check-ignore` succeeds via
`.gitignore`'s `vale/styles/Google/` entry). `vale/.vale.ini.template` and
`vale/styles/config/vocabularies/House/accept.txt` ARE tracked (`git ls-files
vale/` output above). Correct.

## Gates / scope

`git diff a232c62 --stat` (full repo, base a232c62 = the "in-progress"
handoff commit before this task's work landed in c50c625):
```
 .gitignore                                       |  4 ++
 bin/install-vale                                 | 65 ++++++++++++++++++++++++
 specs/prose-review/tasks/02-vale-install.md      | 12 +++++
 vale/.vale.ini.template                          | 15 ++++++
 vale/styles/config/vocabularies/House/accept.txt | 15 ++++++
```
All changed files fall within the task's `Touch: bin/install-vale, vale/,
.gitignore` list plus its own task file. No scope creep found.

## Append-only task-file check

`git diff a232c62 -- specs/prose-review/tasks/*.md` shows only a 12-line
PLAN comment block inserted into `02-vale-install.md` between the
`Touch:` header and `## Goal`. No other task file touched. However: the
`Status:` line remains `in-progress` and none of the four acceptance
checkboxes were ticked, despite the implementation being complete and all
four criteria passing live. This is a process gap (task not marked done /
no evidence-citation lines added), not a criterion failure — flagging it
since the caller's process expects Status + checkboxes to reflect
completed, verified work.

## Repo gate

Repo has no `scripts/check.sh` (per docs/memory: "`~/claude` has no
scripts/check.sh gate" — task acceptance names concrete runnable commands
instead, which were run above). No separate build/lint/test gate applies
beyond the four acceptance commands.
