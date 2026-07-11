# Verification: 02-project-normalization

Verdict: PASS (with process findings — see below)

## Criterion 1: go test ./internal/claude/ passes, hermetic

Command: `cd agentprof && go test ./internal/claude/ -v`

Result: PASS. All tests pass (ok github.com/sticklane/agentprof/internal/claude 0.203s),
including the four relevant fixtures:
- TestCollectHomeDirProjectMapsToHomeFrame — PASS
- TestCollectMktempProjectMapsToTmpFrame — PASS
- TestCollectAgentSidecarDirEmitsNoProjectAndCountsDrop — PASS
- TestCollectAgentWorktreeDirFoldsIntoOwningProject — PASS

Hermeticity check: each test calls `t.Setenv("AGENTPROF_HOME", "/home/testuser")`
(or `/home/testuser` variant) rather than relying on the real `$HOME`; the
sidecar-drop test asserts `skipped >= 1` (counter incremented) and asserts no
`Stack[0]` has an `agent-` prefix — matching "counter incremented, never
emitted as a project."

## Criterion 2: bash agentprof/scripts/check.sh green

Command: `cd agentprof && bash scripts/check.sh`

Output:
```
check: format-check ok
check: lint ok
check: tests ok
```
PASS.

## Goal verification (read implementation, agentprof/internal/claude/claude.go)

- `resolveHome()` consults `os.Getenv("AGENTPROF_HOME")` before falling back to
  `os.UserHomeDir()` — injectable via env override as required.
- `tmpDirRe = ^tmp\.[A-Za-z0-9]{6,}$` — matches the mktemp-shaped spec exactly.
- `agentDirRe = ^agent-[0-9a-fA-F]+$` plus `worktreeSuffixRe` matching
  `/\.claude/worktrees/agent-[0-9a-fA-F]+$` — when the owning project's
  basename is cheaply resolvable from the path prefix, the agent dir folds
  into that project's name (verified by
  TestCollectAgentWorktreeDirFoldsIntoOwningProject → returns "myrepo").
  Otherwise `normalizeProject` returns `drop=true`, and `session.collect`
  returns `(nil, nil, 1, nil)` — no samples, skipped counter incremented by 1,
  never minted as a project name.
- Diff reviewed via `git diff 028a756 -- internal/claude/claude.go` confirms
  this logic actually runs in the `collect` path (not a dead helper) — `home`
  is threaded from `CollectWithReprime` into `sess.collect(reprimeThreshold,
  home)`.

## Scope / Touch check

Files changed since base (35e134b3): `agentprof/internal/claude/claude_test.go`
(committed, +101 lines) and `agentprof/internal/claude/claude.go` (staged,
uncommitted, +60/-5). Both fall within Touch: `agentprof/internal/claude/,
agentprof/testdata/`. No testdata fixtures added, but Touch lists it as
permitted, not mandatory. No scope creep found.

## Append-only task-file check

`git diff 35e134b3cd82d41eaadf56f732380ecc05987507 HEAD -- specs/agentprof-attribution-gaps/tasks/*.md`
→ empty (no changes at all to any task file, including this task's own file).

## Process findings (not acceptance-blocking, but noted)

1. **Task file not updated to reflect completion.** Status line still reads
   `in-progress`; none of the two acceptance checkboxes are ticked; no
   evidence-citation lines were added, despite the implementation clearly
   satisfying both criteria. Per the task file's own append-only contract,
   the worker was expected to tick boxes and update Status on finishing.
2. **Implementation is staged but not committed.** `git status --short` shows
   `M  agentprof/internal/claude/claude.go` as staged-uncommitted, while the
   test file is already committed in a separate prior commit
   (`8c52d80 test: project normalization fixtures ...`). This splits the
   red→green TDD step across an uncommitted boundary — the repo's "Commit on
   Task Completion" convention (CLAUDE.md) is not yet satisfied for this task.

These are process/completeness gaps, not correctness failures — the acceptance
criteria as literally stated (test pass + check.sh green) are both satisfied
by the current working tree. Recommend the task be committed and its Status/
checkboxes updated before being called fully done.
