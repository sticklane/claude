# Quality-gate hook templates

Contents: Stop gate · Auto-format on edit · Protected files ·
Session-scoped alternatives · Sanity rules

Verified against code.claude.com/docs/en/hooks and hooks-guide (July 2026).
Semantics that matter: exit code 2 blocks (exit 1 is non-blocking and
proceeds); `PostToolUse` cannot block (the tool already ran); a PreToolUse
`permissionDecision: "deny"` blocks even in `bypassPermissions` mode.

Setup rules that silently break gates when skipped:

- `chmod +x .claude/hooks/*.sh` — files created by the Write tool are not
  executable, and hooks fail open on script errors.
- The scripts depend on `jq`; check `command -v jq` first and install or
  rewrite without it if absent.
- If `.claude/settings.json` already exists, MERGE the `hooks` key into it —
  never overwrite the file.

## Stop gate (blocks "done" until checks pass)

`.claude/hooks/stop-gate.sh` — replace `npm test` with the project's check;
note the exit status is captured from the check itself, never from a pipe.
Before exiting 2, the hook checks for a **sanctioned stop**: unattended
workers (drain/autopilot dispatch, and the verifier) are contractually
REQUIRED to stop mid-red with a final message beginning with a verdict line
— `DEFERRED`, `BLOCKED`, or `INCOMPLETE`. Without the bypass the gate would
trap them in a block loop they can never satisfy. The hook's stdin JSON
carries `transcript_path`; the installed hook reads the last assistant
message from the transcript tail and runs exactly
`grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'` on its first line — a match
exits 0:

```bash
#!/bin/bash
# Re-runs the check on every stop attempt, including continuation rounds
# (stop_hook_active=true), so the gate only opens when the check is green.
# Loop safety comes from Claude Code's cap: after 8 consecutive blocks
# without progress it force-ends the turn (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP
# raises that if a gate legitimately needs more rounds).
INPUT=$(cat)

# Sanctioned stop: a final message beginning with a verdict line is an
# unattended worker's contractual mid-red stop — let it through.
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty')
if [ -n "$TRANSCRIPT" ] && [ -r "$TRANSCRIPT" ]; then
  LAST=$(tail -50 "$TRANSCRIPT" \
    | jq -rs '[.[] | select(.type == "assistant")] | last
              | .message.content[]? | select(.type == "text") | .text' \
    2>/dev/null)
  if printf '%s' "$LAST" | head -1 | grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'; then
    exit 0
  fi
fi

if ! RESULT=$(npm test 2>&1); then
  echo "Checks failing — keep working. Output (last 20 lines):" >&2
  printf '%s\n' "$RESULT" | tail -20 >&2
  exit 2
fi
exit 0
```

Registration in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/stop-gate.sh",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

Stop hooks fire whenever Claude finishes responding, not only at task
completion — keep the check cheap, or the gate taxes every conversational
turn. If the check is too slow to re-run each round, use the
`stop_hook_active` input field to allow stopping after one forced retry —
but then describe the gate honestly as "one retry", not "until green":

```bash
# $INPUT already captured at the top of the script
if [ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi
```

## Auto-format on edit

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-file.sh"
          }
        ]
      }
    ]
  }
}
```

`.claude/hooks/format-file.sh` (quoted variable — paths with spaces survive;
`// empty` prevents formatting the literal string "null"):

```bash
#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // empty')
[ -n "$FILE" ] && npx prettier --write --ignore-unknown "$FILE"
exit 0
```

Swap the formatter per project (`gofmt -w`, `ruff format`, `cargo fmt --`).

## Protected files

`.claude/hooks/protect-files.sh` — output built with jq so a hostile file
path cannot inject JSON; tighten or extend the pattern list per repo:

```bash
#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // empty')
case "$FILE" in
  .env|.env.*|*/.env|*/.env.*|*package-lock.json|*pnpm-lock.yaml|*.git/*)
    jq -n --arg reason "Protected file: $FILE" \
      '{hookSpecificOutput: {hookEventName: "PreToolUse",
        permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
    ;;
esac
exit 0
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

**Scope honestly**: this matcher covers Edit/Write only. An agent with Bash
can still write via `sed -i` or `cat >` — pair the hook with permission
`deny` rules in settings.json (e.g. `Bash(sed -i *)` or denying Bash write
patterns) if the protection must be hard, and remember hooks fail open on
script errors while permission rules don't.

**TDD variant** (anti-test-gaming, community practice built on the official
deny mechanism): add the project's test glob (e.g. `*.test.ts|*_test.go`)
to the case list while an implementation task is running, after the failing
tests are committed. Remove it for test-authoring work. Same Bash caveat
applies — the committed failing tests are the tamper-evidence either way.

## Session-scoped alternatives

- `/goal all tests in <dir> pass and lint is clean, or stop after 20 turns`
  — a per-session prompt-based Stop hook; the runtime's
  built-in transcript evaluator (Claude Code: Haiku) judges the transcript
  each turn. Conditions must be demonstrable IN the transcript: have the agent
  run the command so the evaluator can see the output. Bound every goal
  with a turn or time clause.
- Prompt-type hooks (`"type": "prompt"`) for judgment calls a script can't
  make; agent-type hooks (experimental) can run tools to verify, e.g.
  "Verify that all unit tests pass. Run the test suite and check results."

## Sanity rules

- Don't mix exit-code and JSON output in one hook: JSON is ignored on exit 2.
- Hooks fail open on script errors — enforce hard denies with permission
  `deny` rules in settings.json, not hooks alone.
- Test every hook by triggering it once before trusting it.
