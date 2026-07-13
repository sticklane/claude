# Evidence — Task 04: align ~/automation/HUMAN.md (cross-repo)

## Cross-repo base SHA (automation)

Recorded BEFORE any edit, from the automation worktree:

```
$ git -C <automation-worktree> rev-parse HEAD
2f0c3ceb72666e7ad49b15778ae5fed51664ba37
```

automation branch: `task/04-automation-align` (worktree cut from `main` @ 2f0c3ce).
Live automation checkout (`/Users/sjaconette/automation`) was NOT touched —
two live interactive sessions were using it, so all edits were made in a
separate `git worktree` under the session scratchpad.

## Diff summary (additions-only, inside the new section)

```
$ git -C <automation-worktree> diff 2f0c3ce -- HUMAN.md
@@ -25,3 +25,5 @@ verified live):
 - **Todoist backlog triage**: ~40 one-off tasks from Apr–May 2026 are still
   overdue (UK ETA, Bloomberg cancellation, …). The morning brief surfaces
   the count; triage them there, or ask for a triage pass any time.
+
+## Agent-filed blockers
```

Diffstat: `HUMAN.md | 2 ++` — **1 file changed, 2 insertions(+), 0 deletions(-)**.
Additions only; the narrative above (title, done-log bullets, Optional
backlog) is byte-for-byte untouched. The added `## Agent-filed blockers`
heading is empty, placed below the human-owned narrative per the bootstrap
rule in `.claude/rules/human-blockers.md`.

automation commit: `1ff5b4d docs: HUMAN.md gains empty Agent-filed blockers section`

## Gate result (automation `scripts/check.sh`)

Docs-only change; ran automation's full gate in the worktree to confirm no
regression:

```
$ bash scripts/check.sh
ruff check .        → All checks passed!
ruff format --check → 51 files already formatted
python3 -m pytest   → 178 passed in 1.96s
```

Gate green. No regression from this docs-only change.
