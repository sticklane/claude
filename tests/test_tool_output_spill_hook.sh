#!/usr/bin/env bash
# Bring the tool-output-spill hook's own suite inside scripts/check.sh, whose
# glob is tests/test_*.sh — without this the hook is ungated. Adds one case
# the string-only fixtures cannot express: a structured (non-string)
# tool_response, the shape Read/Agent/Workflow returns actually carry.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$ROOT/hooks/tool-output-spill/spill-check.sh"

command -v jq >/dev/null 2>&1 || {
  printf 'skip - structured-response case needs jq\n'
  exec bash "$ROOT/hooks/tool-output-spill/test.sh"
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export TMPDIR="$work"

fail=0

big="$(head -c 60000 /dev/zero | tr '\0' 'y')"
out="$(jq -n --arg c "$big" \
  '{session_id:"structured",hook_event_name:"PostToolUse",tool_name:"Read",tool_input:{},tool_response:{file:{content:$c}}}' |
  bash "$HOOK")"

event="$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null)"
if [ "$event" = "PostToolUse" ]; then
  printf 'ok   - structured tool_response over budget is replaced\n'
else
  printf 'FAIL - structured tool_response over budget is replaced (got %q)\n' "$event"
  fail=1
fi

small="$(jq -n '{session_id:"structured",hook_event_name:"PostToolUse",tool_name:"Read",tool_input:{},tool_response:{file:{content:"hi"}}}' |
  bash "$HOOK")"
if [ -z "$small" ]; then
  printf 'ok   - structured tool_response under budget stays silent\n'
else
  printf 'FAIL - structured tool_response under budget stays silent\n'
  fail=1
fi

bash "$ROOT/hooks/tool-output-spill/test.sh" || fail=1
exit "$fail"
