Verdict: PASS

Task: specs/drain-rolling-window/tasks/15-mirror-bash-32-compat-note-to-antigravity-evals.md
Branch: task/15-mirror-bash-32-compat-note
Base commit: 5e3a57bf958fa306d10bc1f21aad219d2c936aa9

## Acceptance criteria

1. Command: `grep -q '3\.2' antigravity/.agents/workflows/evals.md`
   Result: PASS (exit 0)

2. Command: `grep -q 'declare -A' antigravity/.agents/workflows/evals.md`
   Result: PASS (exit 0)

3. Command: `grep -Eqi 'macos|system bash' antigravity/.agents/workflows/evals.md`
   Result: PASS (exit 0)

All three commands run directly against the worktree file (relative to
worktree root) exit 0.

## Placement check

Diff of antigravity/.agents/workflows/evals.md vs base commit:

```
@@ -8,7 +8,9 @@ is `evals/<skill>/<NN-name>/` containing `setup.sh` (builds a fixture
 repo in `$EVAL_DIR`), `prompt.txt` (the user turn, a slash command with
 fixture-relative paths, no `$EVAL_DIR` variables), `assert.sh` (runs
 with CWD the fixture; exit 0 = pass, non-zero with output explaining
-what failed). Antigravity has no headless CLI, so the run step hands the
+what failed). Both scripts run under bare `bash`, and macOS's system bash
+is 3.2 — write them to bash 3.2 (no `declare -A` or other bash-4+ syntax),
+or they misbehave silently rather than erroring. Antigravity has no headless CLI, so the run step hands the
 user Agent Manager launches instead of `claude -p`; `allowed-tools.txt`
 has no Antigravity equivalent and is ignored here.
```

The inserted note is embedded directly in the paragraph describing
`setup.sh`/`assert.sh` (the scenario-authoring passage the task specifies),
immediately after the sentence describing what `assert.sh` does and before
the unrelated sentence about Antigravity's lack of a headless CLI. Not
spuriously placed elsewhere in the file — confirmed via `git diff`, no other
hunks exist in this file.

## Append-only task-file diff check

Command: `git diff 5e3a57bf958fa306d10bc1f21aad219d2c936aa9 -- 'specs/*/tasks/*.md'`

Only one task file changed (the worker's own,
specs/drain-rolling-window/tasks/15-mirror-bash-32-compat-note-to-antigravity-evals.md).
Diff contents:

- `Status: in-progress` -> `Status: done` (allowed: Status flip)
- Three acceptance checkboxes `- [ ]` -> `- [x]` with appended
  `(verifier confirmed)` evidence text (allowed: checkbox ticks +
  evidence-citation lines)

No changes to Goal, Steps, Touch, Budget, or the acceptance criteria text
itself. No other task file (any spec) was touched.

## Touch-list scope check

Command: `git diff 5e3a57bf958fa306d10bc1f21aad219d2c936aa9 --stat`

```
 antigravity/.agents/workflows/evals.md                            | 4 +++-
 .../tasks/15-mirror-bash-32-compat-note-to-antigravity-evals.md   | 8 ++++----
 2 files changed, 7 insertions(+), 5 deletions(-)
```

Exactly two files changed: the Touch-listed
`antigravity/.agents/workflows/evals.md` and the worker's own task file.
No scope creep (no plugin.json bump, no other mirror files touched — task
explicitly notes no plugin bump is needed since this is an antigravity-only
change).

## Summary

- ✓ `grep -q '3\.2' antigravity/.agents/workflows/evals.md` — match
- ✓ `grep -q 'declare -A' antigravity/.agents/workflows/evals.md` — match
- ✓ `grep -Eqi 'macos|system bash' antigravity/.agents/workflows/evals.md` — match
- ✓ Note lives in the scenario-authoring passage, not elsewhere
- ✓ Task-file diff is append-only per worker contract
- ✓ Only Touch-listed files changed (antigravity/.agents/workflows/evals.md + task file)

No gate/build/lint commands apply to this doc-only change; none found in
task file or CLAUDE.md specific to this markdown-only edit.
