# Verification: Task 06 baton-predicate-cross-check

Verdict: PASS

## Criterion 1
Command: `grep -q 'skills/drain/reference.md' tests/test_drain_owner_protocol.sh`
Result: exit 0 (match found — new `REFERENCE_MD="$SCRIPT_DIR/../.claude/skills/drain/reference.md"` line).

## Criterion 2
Command: `bash tests/test_drain_owner_protocol.sh`
Output tail:
```
PASS: (a) CAS flip
PASS: (b) owner lifecycle
PASS: (c) path-scoped commit
PASS: (d) losing claim
PASS: (e) baton adoption predicate
pass: 15 fail: 0
```
Exit code: 0. All five cases (a)-(e) PASS, `fail: 0`.

## Meaningfulness check (not vacuous)
Copied the full worktree to a scratch dir, mutated the shipped predicate in
`.claude/skills/drain/reference.md` (line ~72) from:
  `... matches DRAIN-OWNER.md's.`
to:
  `... matches SESSION-LOG.md's.`
(comparison target changed, grammar otherwise intact), then ran the
unmodified `tests/test_drain_owner_protocol.sh` from that mutated copy
(REFERENCE_MD resolves relative to the script's own location, so it picked
up the mutated file automatically).

Result:
```
FAIL: (e) baton adoption: shipped reference.md still pins the Run-token/DRAIN-OWNER.md predicate adopt() implements
FAIL: (e) baton adoption predicate
pass: 14 fail: 1
EXIT_CODE=1
```

Confirmed: the new assertion added in case (e) genuinely binds the local
`adopt()` predicate to the shipped reference.md text — a divergence in the
pinned grammar (target field changed) fails the suite rather than passing
silently. Not vacuous.

## Diff scope
`git diff ad9b4a4 --stat` → only `tests/test_drain_owner_protocol.sh` changed
(21 insertions, 0 deletions). No other files touched.

## Append-only task-file check
`git diff ad9b4a4 -- 'specs/multi-session-coordination/tasks/*.md'` → empty
(no output at all). This means the task file itself (Status line, checkbox
ticks, evidence-citation lines, plan comment block) was NOT updated by the
worker: `Status:` still reads `in-progress` and both acceptance checkboxes
are still unticked (`- [ ]`), even though the underlying acceptance criteria
now pass. This is not a scope-creep violation (nothing improper was added),
but it is a process gap worth flagging: the task file does not reflect
completed work, so an orchestrator scanning Status/checkboxes would not see
this task as done.

## Gates
No repo-wide `scripts/check.sh` gate was run beyond the specified acceptance
commands, per the task's narrow acceptance criteria (test-script-only
change; no lint/build implications for a bash test file beyond what the
test itself exercises).

## Scope-creep findings
None. Diff is confined to the described cross-check addition inside case
(e) plus the `REFERENCE_MD`/`SCRIPT_DIR` setup lines needed to locate the
shipped file — matches the task's Goal exactly.
