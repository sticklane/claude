# Antigravity hook templates

Format notes (verified against antigravity.google/docs/hooks and community
guides, July 2026): project hooks live in `<root>/.agents/hooks.json`;
global hooks in `~/.gemini/config/hooks.json` (IDE). Both scopes run and
any deny vetoes. Top-level keys are hook NAMES mapping to event objects
(inverted vs Claude Code's event-keyed shape). Matchers are regexes over
internal tool names (`write_to_file`, `replace_file_content`,
`run_command`, `call_mcp_tool`, `"*"`). Hook stdin is JSON
(`hook_event_name`, `cwd`, `toolCall.args`); stdout JSON controls the
outcome: `{"allow_tool": false, "deny_reason": "..."}` to block,
`"additionalContext"` to feed text back to the agent. Default timeout 60s.

Setup rules:

- `chmod +x .agents/hooks/*.sh` — hooks fail open on script errors.
- Scripts depend on `jq`; check `command -v jq` first.
- Use absolute paths or repo-root-relative paths per your build's docs;
  MERGE into an existing hooks.json rather than overwriting.
- Test each hook by triggering it once before trusting it.

## Post-edit format + lint

`.agents/hooks.json`:

```json
{
  "format-and-lint": {
    "PostToolUse": [
      {
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
        "hooks": [
          { "type": "command", "command": ".agents/hooks/post-edit.sh", "timeout": 30 }
        ]
      }
    ]
  }
}
```

`.agents/hooks/post-edit.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.toolCall.args.TargetFile // empty')
[ -z "$FILE" ] && exit 0
npx prettier --write --ignore-unknown "$FILE" >/dev/null 2>&1
if ! LINT=$(npx eslint "$FILE" 2>&1); then
  jq -n --arg ctx "Lint failures in $FILE — fix before proceeding: $LINT" \
    '{additionalContext: $ctx}'
fi
exit 0
```

(Swap formatter/linter per project. The exact args key for the edited file
path may differ by tool/version — dump `$INPUT` to a temp file once to
confirm the shape, then finalize the jq path.)

## Protected files

```json
{
  "protect-files": {
    "PreToolUse": [
      {
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
        "hooks": [
          { "type": "command", "command": ".agents/hooks/protect-files.sh", "timeout": 10 }
        ]
      }
    ]
  }
}
```

`.agents/hooks/protect-files.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.toolCall.args.TargetFile // empty')
case "$FILE" in
  .env|.env.*|*/.env|*/.env.*|*package-lock.json|*pnpm-lock.yaml|*.git/*)
    jq -n --arg reason "Protected file: $FILE" \
      '{allow_tool: false, deny_reason: $reason}'
    exit 0
    ;;
esac
printf '{"allow_tool": true}\n'
exit 0
```

The `*.git/*` entry is a **git-specific** pattern string (git keeps its
metadata under `.git/`), not a VCS-agnostic one — a jj-colocated repo would
add `*.jj/*` to protect the equivalent internal state.

**TDD variant**: add the project's test glob (e.g. `*.test.ts`) to the case
list after the failing tests are committed; remove it for test-authoring
work. Shell writes (`sed -i`, `cat >`) bypass this matcher — pair with the
command blocker below and the Terminal Execution Policy deny list.

## Command blocking

```json
{
  "block-dangerous-commands": {
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          { "type": "command", "command": ".agents/hooks/block-commands.sh", "timeout": 10 }
        ]
      }
    ]
  }
}
```

`.agents/hooks/block-commands.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.toolCall.args.CommandLine // empty')
if printf '%s' "$CMD" | grep -qE 'git push|rm -rf|terraform (apply|destroy)'; then
  jq -n --arg reason "Blocked command pattern: $CMD" \
    '{allow_tool: false, deny_reason: $reason}'
  exit 0
fi
printf '{"allow_tool": true}\n'
exit 0
```

The `git push` entry in this deny pattern is a **git-specific** command
string, not a VCS-agnostic one — a jj-based repo would match its own
push/publish command (e.g. `jj git push`) instead. The pattern is left
git-specific here by design; widening it is a permission-surface change out
of scope for the phrasing pass.

## What replaces the Stop gate

Antigravity's Stop event fires at session end, not turn end, so there is no
per-turn "block done until green" hook. The equivalent discipline:

- Implementation-plan review pause ON (artifact review policy) for core
  work — the human gates the plan, not the exit.
- Walkthrough artifacts must contain the acceptance commands' actual output
  (the verifier skill enforces this in review).
- CI as the hard backstop: the same check commands run on push.

Unattended workers are contractually REQUIRED to end mid-red with a final
message beginning with a verdict line — `DEFERRED`, `BLOCKED`, or (from
the verifier) `INCOMPLETE`. Such an ending is a **sanctioned stop**: the
review-side gates above must not read it as a failed exit. This mirrors the Claude Code
gate's Stop-hook bypass, which reads the last assistant message from the
transcript tail and runs `grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'` on
its first line before exiting 2. Antigravity's hook stdin JSON
(`hook_event_name`, `cwd`, `toolCall.args`) carries no transcript path, so
any session-end script you add must read the final message from the
walkthrough artifact instead — or leave the check review-side, where the
verifier skill applies the same verdict-line rule.
