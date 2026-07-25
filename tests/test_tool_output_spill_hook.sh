#!/usr/bin/env bash
# Bring the tool-output-spill hook's own suite inside scripts/check.sh, whose
# glob is tests/test_*.sh — without this the hook is ungated. Adds one case
# beyond the suite: the emitted replacement, parsed as JSON, is exactly the
# Bash output object the docs require ("The value must match the tool's
# output shape" — a mismatched replacement is silently ignored for built-in
# tools, making the hook a no-op).
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$ROOT/hooks/tool-output-spill/spill-check.sh"

command -v jq >/dev/null 2>&1 || {
  printf 'skip - schema case needs jq\n'
  exec bash "$ROOT/hooks/tool-output-spill/test.sh"
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export TMPDIR="$work"

fail=0

big="$(head -c 60000 /dev/zero | tr '\0' 'y')"
shape="$(jq -n --arg so "$big" \
  '{session_id:"schema",hook_event_name:"PostToolUse",tool_name:"Bash",
    tool_input:{command:"true"},
    tool_response:{stdout:$so,stderr:"",interrupted:false,isImage:false}}' |
  bash "$HOOK" |
  jq -r '.hookSpecificOutput.updatedToolOutput
    | [type, (.stdout|type), (.stderr|type), (.interrupted|type), (.isImage|type),
       (keys | sort | join(","))] | join("|")' 2>/dev/null)"

if [ "$shape" = "object|string|string|boolean|boolean|interrupted,isImage,stderr,stdout" ]; then
  printf 'ok   - replacement is the Bash output object the docs require\n'
else
  printf 'FAIL - replacement is the Bash output object the docs require (got %s)\n' "$shape"
  fail=1
fi

bash "$ROOT/hooks/tool-output-spill/test.sh" || fail=1
exit "$fail"
