# Verification: task/02-screen-fix

Verdict: PASS

## Criterion 1
Command: `bash .claude/skills/drain/screen-stub.sh specs/agentprof-attribution-gaps/tasks/08-pending-match-meta-sidechain-investigation.md`
Output: `screen-stub: clean`, exit 0. PASS.

## Criterion 2
Command: `bash .claude/skills/drain/screen-stub-fixtures/run.sh`
Output: `screen-stub-fixtures: PASS (positive refused via abs-path-outside-repo only; negative clean)`, exit 0. PASS.

## Criterion 3 (MANUAL rule-isolation)
Copied screen-stub.sh to scratch, neutralized `re_abspath` to `$^` (never matches),
pointed a copy of run.sh's `screen` var at it (edited script in place, ran, then
restored original from a pre-saved backup — no committed change; `git diff` on
screen-stub.sh after restore showed zero delta).
With the rule neutralized: run.sh output:
```
  FAIL positive: expected exit 1 (refused), got 0
  FAIL positive: expected abs-path-outside-repo in refusal, got: screen-stub: clean
```
exit 1 (test correctly fails). Confirms rule isolation: the positive fixture is
refused ONLY via abs-path-outside-repo, and deleting/neutralizing that rule alone
makes the fixture test fail. PASS.

## R2 intent spot-check
- `cat /etc/passwd` -> REFUSED via abs-path-outside-repo (exit 1)
- `read ~/.ssh/id_rsa` -> REFUSED via abs-path-outside-repo (exit 1)
- `data lives in /etc/foo` (bare descriptive mention) -> clean (exit 0)
Confirms instruction-shaped vs. bare-mention discrimination works as intended.

Diff of re_abspath line (only line touched among the four rules):
```
-re_abspath='(^|[^[:alnum:]])(/etc/|/root/|/var/|/usr/|/bin/|/sbin/|/sys/|/proc/|/dev/|~/)'
+re_abspath='(^|[^[:alnum:]])(read|write|copy|run|execute|exec|open|delete|remove|cat|move|access|fetch|load|save|dump|exfiltrate|upload|download)[[:space:]]+([[:alnum:]._-]+[[:space:]]+){0,3}(/etc/|/root/|/var/|/usr/|/bin/|/sbin/|/sys/|/proc/|/dev/|~/)'
```
re_ignore, re_agent, re_tool unchanged (no diff lines for those variables) —
regression requirement satisfied.

## Task-file append-only check
`git diff aef3c5e -- specs/drain-forward-progress/tasks/02-screen-fix.md` shows only
a PLAN comment block inserted above `## Goal`. Status line unchanged (`in-progress`,
not flipped to done). No checkboxes ticked, no evidence-citation lines added yet.
No edits to Goal/Steps/Touch/Budget/acceptance text. No other task file touched.

## Scope / Touch check
`git diff aef3c5e --stat`: only screen-stub.sh, screen-stub-fixtures/{run.sh,
positive-instruction-abspath.md, negative-mention-abspath.md}, and the task file's
PLAN block changed — matches Touch: exactly. No scope creep (no antigravity mirror
edit, no plugin.json bump — not required since the task's own Touch doesn't list
them, though CLAUDE.md's mirror convention would normally require a closing task
to carry that; flagging as a note, not a defect of this task).

## Gates
No repo-wide scripts/check.sh found for this toolkit repo per CLAUDE.md note
("~/claude has no scripts/check.sh gate" — acceptance is via named runnable
commands, which were run above).
