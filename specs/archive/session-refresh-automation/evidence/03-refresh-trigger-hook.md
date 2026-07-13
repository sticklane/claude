# Verification: task 03 — refresh trigger hook

Verdict: PASS

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-af10f6031f1900f44
Branch: task/03-refresh-trigger-hook

## Criterion 1 — test.sh all cases pass, exit 0

Command: `bash hooks/session-refresh/test.sh`

```
ok   - over-budget (re-prime arm) emits /handoff directive
ok   - over-budget (context arm) emits /handoff directive
ok   - under-budget produces empty stdout
ok   - under-budget exits 0
ok   - session absent from summary produces empty stdout
ok   - missing agentprof binary produces empty stdout
ok   - missing agentprof binary exits 0
ok   - agentprof error produces empty stdout
ok   - agentprof error exits 0

9 passed, 0 failed
EXIT:0
```
PASS — 9/9 cases pass (superset of the "over/under/absent" 3-case minimum), exit 0.

## Criterion 2 — `/handoff` directive present in the hook script

Command: `grep -c '/handoff' hooks/session-refresh/*.sh`

```
hooks/session-refresh/test.sh:6
hooks/session-refresh/refresh-check.sh:2
```
PASS — refresh-check.sh (the shipped hook) has 2 occurrences, ≥1.

## Criterion 3 — README documents settings.json wiring

Command: `grep -ci 'settings.json' hooks/session-refresh/README.md`

Output: `2`
PASS — ≥1.

## Criterion 4 — directive appears ONLY on the over-budget path

Read of `hooks/session-refresh/test.sh`: confirms cases 3 ("under-budget produces
empty stdout"), 4 ("session absent from summary produces empty stdout"), 5
("missing agentprof binary produces empty stdout"), and 6 ("agentprof error
produces empty stdout") all assert `[ -z "$OUT" ]` (zero-byte stdout), while
cases 1 and 2 (both over-budget arms: re-prime and context) assert
`grep -q '/handoff'` on stdout. This matches exactly the paths required by the
criterion (under-budget, session-absent, agentprof-absent, agentprof-erroring
→ empty; both over-budget arms → directive).

Hand sanity-check with the bundled fake double
(`hooks/session-refresh/fixtures/fake-agentprof.sh`):

Command (under-budget, `fixtures/under.json`):
```
OUT=$(printf '{"session_id":"test-session",...}' | \
  AGENTPROF_BIN=.../fixtures/fake-agentprof.sh \
  FAKE_SUMMARY_SRC=.../fixtures/under.json \
  bash refresh-check.sh)
echo "bytes: ${#OUT}"
```
Output: `bytes: 0` — zero bytes on stdout, confirmed by hex dump (empty).

Command (over-budget, `fixtures/over-reprime.json`, reprime_count=5 ≥ budget 3):
```
OUT2=$(... FAKE_SUMMARY_SRC=.../fixtures/over-reprime.json bash refresh-check.sh)
echo "bytes: ${#OUT2}"
printf '%s' "$OUT2" | grep -c '/handoff'
```
Output: `bytes: 371`, `grep -c '/handoff'` → `1`.

PASS.

## Shell-out / stdin confirmation

`hooks/session-refresh/refresh-check.sh`:
- Line 30: `sid="$(jq -r '.session_id // empty' 2>/dev/null)"` reads stdin JSON
  directly (no `<` redirection, no argument — it consumes the hook's stdin
  payload) for the session id.
- Lines 34-36: resolves the `agentprof` binary (`AGENTPROF_BIN` override, else
  `command -v agentprof`); silent exit 0 if absent.
- Line 49: `"$bin" claude --since "$since" --summary "$summary" -o /dev/null`
  — shells out to the real `agentprof` binary; the hook does not re-implement
  the re-prime/p90_ctx computation, it only jq-extracts fields from
  agentprof's own summary output (lines 53-56). Confirms the header comment's
  claim ("agentprof is the single source of the re-prime definition... it
  shells out").

Confirmed: hook shells out to agentprof and reads session id from stdin JSON.

## Append-only task-file check

Command:
```
git diff 1f7dcac082b5d13a475e7633e4cac31fc5bc0769 -- specs/session-refresh-automation/tasks/03-refresh-trigger-hook.md
```

Output: a single hunk inserting the `<!-- PLAN (build, delete at close-out) ... -->`
comment block immediately after the `Touch:` header line. No other lines
changed — Goal, Steps, Touch, Budget, Status, and all four Acceptance
criterion texts are byte-identical to the base commit. No checkbox ticks, no
evidence-citation lines, and no Status change were made either (see Finding
below).

PASS — the only change is the plan comment block, which is an allowed
addition.

## Gates

No repo-wide `scripts/check.sh` exists at the worktree root scoped to this
hook; `hooks/session-refresh/test.sh` is the task's own gate and was run
above (green). No lint/build config applies to this bash-only directory.

## Scope-creep check

`git diff --name-only 1f7dcac082b5d13a475e7633e4cac31fc5bc0769 HEAD`:
```
hooks/session-refresh/README.md
hooks/session-refresh/fixtures/fake-agentprof.sh
hooks/session-refresh/fixtures/over-ctx.json
hooks/session-refresh/fixtures/over-reprime.json
hooks/session-refresh/fixtures/under.json
hooks/session-refresh/refresh-check.sh
hooks/session-refresh/test.sh
specs/session-refresh-automation/tasks/03-refresh-trigger-hook.md
```
All files fall under `hooks/session-refresh/` (the task's `Touch:` scope)
plus the task file itself. No `.claude/settings*.json`, `.claude/skills/`,
or `.claude/rules/` edits — matches the task's explicit "Do NOT edit" note.
No scope creep found.

## Findings (non-blocking)

1. The task file's `Status:` header still reads `in-progress` and all four
   `## Acceptance` checkboxes remain unticked (`- [ ]`), despite the
   implementation being functionally complete and all criteria passing. The
   `<!-- PLAN ... -->` comment block (marked "delete at close-out") was also
   not removed. This is a process/close-out gap, not a functional failure —
   flagging per the verification charter since the task's own convention
   (Status/checkbox/plan-cleanup at close-out) was not followed, even though
   the append-only diff check itself passes (no disallowed edits were made).
