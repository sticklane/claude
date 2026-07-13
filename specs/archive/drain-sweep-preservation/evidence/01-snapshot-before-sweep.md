# Verification: 01-snapshot-before-sweep

Verdict: PASS

Base commit compared against: 45eb39edd695173644de70906c2d838daf7033ec
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-accb7fccd8d966fb7

## 1. Acceptance commands (run from repo root, cd into worktree first)

1. `grep -q 'status --porcelain' .claude/skills/drain/reference.md`
   → exit 0 (PASS). Match at reference.md:110 ("run `git -C <worktree>
   status --porcelain`").

2. `grep -q 'wip(rescue)' .claude/skills/drain/reference.md`
   → exit 0 (PASS). Match at reference.md:114-115 (`git commit --no-verify
   -m "wip(rescue): <task> — swept with uncommitted work"`). `git add -A`
   appears at line 112-113 in the SAME rescue-procedure paragraph
   (lines 106-123, one unbroken paragraph) — confirmed same procedure.

3. `grep -qi 'snapshotting uncommitted' .claude/skills/drain/SKILL.md`
   → exit 0 (PASS). Match at SKILL.md:88 ("snapshotting uncommitted
   worktree changes per reference.md's rescue procedure").

4. `grep -qi 'preserved in the rescue snapshot' .claude/skills/drain/SKILL.md`
   → exit 0 (PASS). Match at SKILL.md:281 ("preserved in the rescue
   snapshot when a dead run is swept dirty; deliberately discarded
   branches ... remain discarded").

5. `claude plugin validate .`
   → "Validating marketplace manifest: .../.claude-plugin/marketplace.json"
     "✔ Validation passed", exit 0 (PASS).

6. `./specs/status.sh`
   → exit 0 (PASS). Output parsed cleanly, ended with a TOTAL summary
   (done: 28, draft: 7, in-progress: 1, pending: 4, all: 40). No errors.

All 6 acceptance commands: PASS.

## 2. Intent match (Goal/Steps vs actual diff)

Diff of the two touched skill files (against base 45eb39e):

```
reference.md (Status field semantics rescue paragraph):
+ Before force-removing a worktree, snapshot any uncommitted work so the
+ sweep never destroys it: run `git -C <worktree> status --porcelain`, and
+ if it is non-empty, commit a WIP snapshot on the run's branch from inside
+ the worktree — exactly `git add -A` from the worktree root ... then
+ `git commit --no-verify -m "wip(rescue): <task> — swept with uncommitted
+ work"` — so the snapshot tip becomes that branch's shortsha. Then
+ force-remove each worktree FIRST ...
```
(a) CONFIRMED — dirty-check (`status --porcelain`) + WIP-snapshot
(`git add -A` + `git commit --no-verify -m "wip(rescue): ..."`) inserted
immediately before "force-remove each worktree FIRST"; text explicitly ties
shortsha to the snapshot tip ("the snapshot tip becomes that branch's
shortsha").

```
SKILL.md step 1:
- ... force-removing each worktree first, then flip the task to `pending`
+ ... snapshotting uncommitted worktree changes per reference.md's rescue
+ procedure and force-removing each worktree first, then flip the task to
+ `pending`
```
(b) CONFIRMED — sweep sentence now defers to reference.md's rescue
procedure via "snapshotting uncommitted".

```
SKILL.md step 3:
- (Worktree writes are discarded with failed branches; this record
-  survives because drain, the single writer, writes it in the main
-  checkout.)
+ (Worktree writes are preserved in the rescue snapshot when a dead run is
+  swept dirty; deliberately discarded branches — slot-machine losers,
+  non-winning tournament candidates — remain discarded. This record
+  survives regardless because drain, the single writer, writes it in the
+  main checkout.)
```
(c) CONFIRMED — reworded exactly per Goal: dirty-sweep worktree writes now
"preserved in the rescue snapshot"; deliberately-discarded branches
(slot-machine losers, non-winning tournament candidates) explicitly remain
discarded.

```
reference.md Residual risk (accepted):
  ... do NOT add worker-side heartbeats to close this gap (rejected — see
  the spec's Out of scope).
+ A false sweep now also snapshots the live worker's uncommitted writes
+ into the rescue branch, so the accepted risk is losing the RUN, not the
+ work.
```
(d) CONFIRMED — false-sweep-now-snapshots sentence appended verbatim to
intent (accepted risk reframed as losing the RUN, not the work).

All four Goal/Steps items (a)-(d): CONFIRMED matching intent.

## 3. Scope check

`git diff 45eb39edd695173644de70906c2d838daf7033ec --stat` (run inside the
worktree):

```
 .claude/skills/drain/SKILL.md                                      | 15 +++++++++------
 .claude/skills/drain/reference.md                                  | 13 +++++++++++--
 specs/drain-sweep-preservation/tasks/01-snapshot-before-sweep.md    | 16 ++++++++++++++++
 3 files changed, 36 insertions(+), 8 deletions(-)
```

Only the two Touch-listed drain skill files plus the task file itself
changed. No edits to:
- worker prompts (task 03) — absent from diff
- an "Environment kill" section (task 02) — absent from diff
- `.claude-plugin/plugin.json` — absent from diff
- the antigravity mirror — absent from diff

No scope-creep / out-of-scope edits found.

## 4. Append-only task-file check

`git diff 45eb39edd695173644de70906c2d838daf7033ec -- specs/drain-sweep-preservation/tasks/01-snapshot-before-sweep.md`

Full diff is a single insertion: a `<!-- PLAN (build step 1): ... -->`
HTML comment block inserted between the `Touch:` header line and the
`## Goal` heading. No other lines changed — Status line unchanged
(`in-progress`), Goal/Steps/Touch/Budget/acceptance-criterion text
byte-for-byte unchanged, no checkbox ticked, no evidence-citation lines
added.

This is within the append-only allowance ("maintain its plan comment
block"). No read-only text was altered. PASS on the append-only check.

Observation (not a failure): the Status line was left as `in-progress`
and none of the 6 acceptance checkboxes were ticked/cited with evidence,
even though all 6 acceptance commands pass when run directly. This means
the task file itself does not yet reflect completion — process note for
the orchestrator, not a criterion violation, since the append-only rule
only restricts what workers may change, not requiring they change it.

## Gates

No repo-wide build/lint/test gate applies beyond the acceptance commands
above (docs-only change; task file states "Docs-only diff; no test-shaped
criteria").

## Overall verdict: PASS

All 6 acceptance commands pass verbatim. All four intent items (a)-(d)
confirmed in the actual diff. No scope creep. Task file respects the
append-only contract (only the plan-comment block was added).
