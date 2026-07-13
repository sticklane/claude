# Verification: 09-fix-stale-group-mode-antigravity-handoff

Verdict: PASS

## Criteria

1. `grep -c "group throughput mode" antigravity/.agents/skills/breakdown/SKILL.md`
   Output: `0` (grep exit code 1, expected — no match found).
   Result: PASS (count == 0, as required).

2. `grep -ci "rolling.window" antigravity/.agents/skills/breakdown/SKILL.md`
   Output: `3` (>= 1 required).
   Result: PASS.

## Diff review (scope)

`git diff -- antigravity/.agents/skills/breakdown/SKILL.md` (uncommitted working-tree change):

```
@@ -120,5 +120,5 @@ grammar itself lives in drain's reference — cite it, don't restate it here.

 Tell the user: run `/build specs/<slug>/tasks/01-*.md` in a new conversation
 per task, or apply the drain workflow (`.agents/workflows/drain.md`) to work
-the queue — its group throughput mode hands you concurrent Agent Manager
-launches for an independent group.
+the queue — its rolling window hands you concurrent Agent Manager
+launches for the unblocked tasks in flight.
```

Only the "Hand off" section's two lines changed; nothing else in SKILL.md or
elsewhere in the repo was touched (`git status --porcelain` shows only this
one file modified, no other paths).

The replacement is grammatical and semantically accurate: cross-checked
against `antigravity/.agents/workflows/drain.md`, which defines "a rolling
window of up to W fresh agents in flight ... each on an unblocked task" —
the new SKILL.md wording ("its rolling window hands you concurrent Agent
Manager launches for the unblocked tasks in flight") matches that
terminology rather than keyword-stuffing "rolling window" in unrelated to
the sentence's meaning.

## Task-file append-only check

Base commit: 80fc23a26f785cedfa1bc1566a843e0f634e6d8a
`git merge-base HEAD 80fc23a26f785cedfa1bc1566a843e0f634e6d8a` → identical to
the base commit itself, i.e. HEAD == base (the base commit is the tip of the
branch; the fix is present only as an uncommitted working-tree change).

`git diff 80fc23a26f785cedfa1bc1566a843e0f634e6d8a -- 'specs/*/tasks/*.md'`
→ empty output. No task-file changes exist yet relative to base (task file
`Status: in-progress`, acceptance checkboxes still unchecked, no evidence
lines added). This means there is nothing to check for scope violation in
the task file — but it also means the worker has not yet updated the task
file's Status/checkboxes/evidence to reflect the completed fix. Noting this
as an observation, not a failing criterion (not one of the two acceptance
commands specified), but the task is not fully "closed" per the toolkit's
own bookkeeping conventions until Status/checkboxes/evidence are updated
and committed.

## Scope creep

None found. Only `antigravity/.agents/skills/breakdown/SKILL.md` is modified
in the working tree (`git status --porcelain`), and only the two lines in
the "Hand off" section changed within that file. Touch list in the task
file (`Touch: antigravity/.agents/skills/breakdown/SKILL.md`) matches
exactly.

## Gates

This is a one-line docs-only change to a Markdown skill file; no
lint/build/test gate applies (no code changed). The repo's
`bash evals/lint-ultra-gate.sh` gate applies only to the four ultra-path
skills (critique, drain, build, idea) — `breakdown` is not one of them, so
it does not apply here.

## Summary

Both acceptance commands pass exactly as specified, the fix is a clean,
grammatical, correctly-scoped one-line replacement matching current
rolling-window terminology, and no scope creep exists. The only open item
is that the task file itself (Status, checkboxes, evidence) has not yet
been updated/committed to reflect completion — this is a process/bookkeeping
gap, not an acceptance-criteria failure.
