Verdict: PASS

## Criterion 1: stale "group mode" reference removed
Command: `grep -c "drain's own group mode" .claude/skills/drain/SKILL.md`
Output: `0`
Result: PASS

## Criterion 2: rolling-window mention present, in push-guard parenthetical vicinity
Command: `grep -n "rolling-window" .claude/skills/drain/SKILL.md`
Output:
```
165:specs/drain-rolling-window/SPEC.md's Parallelization section and emitted by
249:  (canonical; build cites this, and drain's own rolling-window merges follow
```
Line 249 is exactly the push-guard parenthetical line named in the task (Touch/Steps reference "line 249"). Result: PASS

## Diff minimality / scope
Command: `git diff ff0aca3 -- .claude/skills/drain/SKILL.md`
```
@@ -246,7 +246,7 @@ itself flips the status to `done` and commits the flip.)
   Then **push `main` immediately after this commit** (`git push`) so the
   merged, verifier-PASSED work is backed up the moment it lands rather
   than sitting on local `main` for a human to push by hand. **Push guard
-  (canonical; build cites this, and drain's own group mode follows
+  (canonical; build cites this, and drain's own rolling-window merges follow
   it, extended here to every drain bookkeeping commit — not only DONE
   merges — since a concurrent session's `pull --rebase` has been observed
   to drop unpushed drain commits: docs/memory/concurrent-session-collision.md):**
```
`git diff ff0aca3 --stat`: `.claude/skills/drain/SKILL.md | 2 +-` (1 file changed, 1 insertion, 1 deletion) — only file touched, matches Touch: .claude/skills/drain/SKILL.md. Wording change is grammatically consistent (singular "follows"→plural "follow" adjusted correctly for "merges"). No scope creep. Result: PASS

## Append-only task-file check
Command: `git diff ff0aca3 -- specs/drain-rolling-window/tasks/`
Output: (empty — no changes to any task file, including task 07's own)
Result: PASS (trivially — nothing changed outside the allowed set, though note task 07's own Status/checkboxes were NOT updated to reflect completion — see note below)

## Other observations
- `git status`: only `.claude/skills/drain/SKILL.md` modified, working tree otherwise clean.
- No other stale-text sites in `.claude/skills/drain/SKILL.md` or `antigravity/` mirror reference this string; other hits for "drain's own group mode" are in archived/historical spec files (specs/archive/routing-merge-hardening/) and in task 01/07's own descriptive prose (not code under Touch) — out of scope, correctly untouched.
- Note (not a criterion failure, but worth flagging to the caller): task file `specs/drain-rolling-window/tasks/07-fix-stale-group-mode-reference.md` still shows `Status: in-progress` and both acceptance checkboxes unticked, despite the underlying fix being complete and verified. The task file itself was not updated with evidence/status — the caller may want the worker to close this out before merge.

## Overall verdict: PASS
All acceptance criteria verified by direct command execution. Diff scoped exclusively to the one-line wording fix in the push-guard parenthetical. No scope creep. Append-only task-file constraint holds (no task file changes at all).
