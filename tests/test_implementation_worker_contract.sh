#!/usr/bin/env bash
# Tests the .claude/agents/implementation-worker.md contract: like scout
# (<=300 words) and verifier ("under a page"), this agent file must state its
# own output-budget stance rather than staying silent — and because its
# stance is "the dispatch prompt owns the cap", it must cite the dispatch
# prompt that carries the number instead of inventing one.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="$TOOLKIT_DIR/.claude/agents/implementation-worker.md"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1"
  fi
}

# body: everything after the closing frontmatter fence.
body="$(awk 'f>1; /^---$/{f++}' "$AGENT")"

# 1. The file states an output-budget stance at all.
budget_para="$(printf '%s\n' "$body" | awk '
  /output budget/ {found=1}
  found && NF {buf = buf $0 " "}
  found && !NF {exit}
  END {print buf}
')"
[ -n "$budget_para" ]
check "agent file states an output-budget stance" $?

# 2. That stance names where the cap actually lives.
printf '%s' "$budget_para" | grep -q "drain/reference.md"
check "output-budget stance cites drain/reference.md as the cap's home" $?

# 3. It explains the ownership, not just the location: the dispatch prompt
#    owns the cap because this agent's output shape varies by caller.
printf '%s' "$budget_para" | grep -qi "dispatch prompt"
check "output-budget stance attributes ownership to the dispatch prompt" $?

printf '%s' "$budget_para" | grep -qi "vary\|varies\|varying"
check "output-budget stance explains why (output shape varies by caller)" $?

# 4. The change is additive: frontmatter contract and the two existing
#    self-contained/authoritative sentences survive.
frontmatter="$(awk '/^---$/{f++; next} f==1' "$AGENT")"
missing_keys=0
for key in name description tools disallowedTools model; do
  printf '%s\n' "$frontmatter" | grep -q "^${key}:" || missing_keys=1
done
check "frontmatter still declares name/description/tools/disallowedTools/model" "$missing_keys"

[ "$(grep -c "self-contained" "$AGENT")" -eq 2 ]
check "both 'self-contained' sentences are preserved" $?

grep -q "authoritative" "$AGENT"
check "the 'authoritative' dispatch-prompt sentence is preserved" $?

echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
