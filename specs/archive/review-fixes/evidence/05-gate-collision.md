# Verification evidence — Task 05: Gate Stop hook sanctioned-stop bypass

Verifier run: 2026-07-03, working tree at
/Users/sjaconette/claude/.claude/worktrees/agent-a36c98e97197e07a3
(branch task/05-gate-collision, HEAD 75d8ece "drain: task rf-05 in-progress",
uncommitted working-tree changes under review).

## Verdict

PASS

## Acceptance criteria

All commands run from the worktree root.

### Criterion 1 — bypass contract documented in gate reference

```
grep -q "sanctioned stop" .claude/skills/gate/reference.md \
  && grep -q "DEFERRED" .claude/skills/gate/reference.md \
  && grep -q "INCOMPLETE" .claude/skills/gate/reference.md
```
Exit 0. ✓ Read the Stop-gate section: it defines "sanctioned stop",
names all three verdict words, and documents the exact grep
(`grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'` on the first line of the
last assistant message).

### Criterion 2 — mechanism named (transcript tail)

```
grep -q "transcript" .claude/skills/gate/reference.md
```
Exit 0. ✓ Prose states the hook's stdin JSON carries `transcript_path`
and the hook reads the last assistant message from the transcript tail
before exiting 2; the embedded script block implements exactly that
(jq `.transcript_path // empty`, `tail -50` + jq filter for last
assistant text, grep on first line, exit 0 on match).

### Criterion 3 — gate SKILL.md names the bypass

```
grep -qi "sanctioned" .claude/skills/gate/SKILL.md
```
Exit 0. ✓ One added sentence in the Stop-gate bullet: verdict-line final
message is a sanctioned stop; rationale (unattended workers stop mid-red
by contract, blocking traps them in a loop); points to reference.md.

### Criterion 4 — interaction notes in autopilot + drain references

```
grep -qi "sanctioned stop" .claude/skills/autopilot/reference.md \
  && grep -qi "sanctioned stop\|gate.*hook" .claude/skills/drain/reference.md
```
Exit 0. ✓ Confirmed by reading, not grep alone:
- autopilot/reference.md (after the walk-away prompt template, before the
  Headless section): a 6-line "Gate interaction:" paragraph — walk-away
  sessions in gated repos rely on the sanctioned stop bypass; without it
  the hook would block the verdict message the orchestrator needs.
- drain/reference.md (after the worker verdict contract block): a 6-line
  "Gate interaction:" paragraph — worker verdicts DEFERRED/BLOCKED (and
  verifier INCOMPLETE) exit the hook 0 even while checks are red, so
  contractual mid-red stops reach drain instead of looping.
Both are genuine, purpose-written notes, not incidental text matches.

### Criterion 5 — antigravity mirror

```
grep -q "sanctioned stop" antigravity/.agents/skills/gate/reference.md
```
Exit 0. ✓ Mirror adds a sanctioned-stop paragraph adapted to Antigravity's
hook JSON shape: notes Antigravity's hook stdin (`hook_event_name`, `cwd`,
`toolCall.args`) carries no transcript path, so the verdict-line rule
applies review-side / via walkthrough artifact. antigravity gate SKILL.md
also mirrors the one-sentence note.

## Functional test of templates/stop-gate.sh

Ran the actual script with synthetic hook JSON + JSONL transcripts in
scratch (`/private/tmp/claude-501/.../scratchpad/gate05`), against a
scratch git repo whose `scripts/check.sh` exits 1 (red):

| Case | Expected | Observed |
|---|---|---|
| Last assistant msg first line `DEFERRED\n...` | exit 0 | exit 0 |
| `BLOCKED: ...` | exit 0 | exit 0 |
| `INCOMPLETE\n...` | exit 0 | exit 0 |
| Normal "done" message, checks red | exit 2 | exit 2 |
| Verdict word mid-message, not first line | exit 2 | exit 2 |
| `DEFERREDX ...` (word-boundary) | exit 2 | exit 2 |
| Earlier msg has verdict, LAST msg normal | exit 2 | exit 2 |
| No transcript_path in hook JSON, checks red | exit 2 | exit 2 |
| Normal message, checks green | exit 0 | exit 0 |

9/9 correct. The bypass reads `transcript_path` from stdin JSON, extracts
the LAST assistant message only, matches `^(DEFERRED|BLOCKED|INCOMPLETE)\b`
on its first line, and fails closed (still blocks) when the transcript is
missing or unreadable.

The documented script block in .claude/skills/gate/reference.md implements
the same logic (INPUT capture at top, same jq extraction, same grep); the
later `stop_hook_active` example was updated to reuse `$INPUT` instead of
a second `cat` — consistent.

## Standard gates

- No repo-wide test/lint/build command; CLAUDE.md's testing guidance is
  live-session testing plus `/evals` for skills with a stored evalset.
  `evals/` contains an evalset only for `breakdown`; gate/autopilot/drain
  have none, so /evals is not applicable to this change.
- templates/stop-gate.sh passes `bash -n` implicitly (executed 9 times
  without syntax error).

## Scope findings (informational, non-blocking)

1. `templates/stop-gate.sh` is modified but absent from the task file's
   Touch list. The task prose says "the installed hook greps the
   transcript tail", and the verification request explicitly directed
   functional testing of this file, so it is treated as in-scope; noted
   for the record.
2. Repo convention (CLAUDE.md): bump `.claude-plugin/plugin.json` version
   "whenever skill behavior changes". Version remains 0.6.1 — correctly
   NOT bumped, since plugin.json is outside the Touch list; reporting the
   convention rather than expecting the edit.
3. `specs/review-fixes/tasks/05-gate-collision.md` Status flip to
   in-progress was committed at HEAD by drain, not part of the reviewed
   working-tree diff.
4. No test files were modified; acceptance checks are doc greps, and the
   docs are substantive (not keyword-stuffed to satisfy the greps).

Working-tree diff: 7 files, +76/−4 — the six Touch files plus
templates/stop-gate.sh. No other changes.
