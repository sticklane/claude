# Quality-gate hook templates

Verified against code.claude.com/docs/en/hooks and hooks-guide (July 2026).
Semantics that matter: exit code 2 blocks (exit 1 is non-blocking and
proceeds); `PostToolUse` cannot block (the tool already ran); a PreToolUse
`permissionDecision: "deny"` blocks even in `bypassPermissions` mode.

## Stop gate (blocks "done" until checks pass)

`.claude/hooks/stop-gate.sh` — replace the check command; keep the guard:

```bash
#!/bin/bash
INPUT=$(cat)
# Anti-loop guard: if we already triggered a continuation, allow stopping.
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi
RESULT=$(npm test 2>&1 | tail -20)
if [ $? -ne 0 ]; then
  echo "Checks failing — keep working. Output:" >&2
  echo "$RESULT" >&2
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

Notes: Stop hooks fire whenever Claude finishes responding, not only at task
completion — keep the check cheap. Claude Code overrides the hook after 8
consecutive blocks without progress; raise with
`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` if a gate legitimately needs more rounds.

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
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write --ignore-unknown"
          }
        ]
      }
    ]
  }
}
```

Swap the formatter per project (`gofmt -w`, `ruff format`, `cargo fmt --`).

## Protected files (deny even in bypassPermissions)

`.claude/hooks/protect-files.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
case "$FILE" in
  *.env*|*package-lock.json|*pnpm-lock.yaml|*.git/*)
    cat <<JSON
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
 "permissionDecision": "deny",
 "permissionDecisionReason": "Protected file: $FILE"}}
JSON
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

**TDD variant** (anti-test-gaming, community practice built on the official
deny mechanism): add the project's test glob (e.g. `*.test.ts|*_test.go`)
to the case list while an implementation task is running, after the failing
tests are committed. Remove it for test-authoring work.

## Session-scoped alternatives

- `/goal all tests in <dir> pass and lint is clean, or stop after 20 turns`
  — a per-session prompt-based Stop hook (Haiku judges the transcript each
  turn). Conditions must be demonstrable IN the transcript: have the agent
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
