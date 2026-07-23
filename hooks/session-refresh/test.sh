#!/usr/bin/env bash
# Unit tests for refresh-check.sh — the session-refresh prompt-submit hook.
# Drives the hook against synthetic transcript JSONL fixtures (fixtures/),
# asserting the over-budget directive appears on exactly the over-budget
# path and nowhere else. Never touches real session data.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/refresh-check.sh"
FIX="$DIR/fixtures"

pass=0
fail=0

# stdin_for <transcript-path> — a synthetic UserPromptSubmit hook payload.
stdin_for() {
  printf '{"session_id":"test-session","transcript_path":"%s","hook_event_name":"UserPromptSubmit","prompt":"go"}' "$1"
}

# run_hook <transcript-path> [env assignments...] — invoke the hook,
# capturing stdout. Sets OUT and RC.
run_hook() {
  local transcript="$1"
  shift
  OUT="$(stdin_for "$transcript" | env "$@" bash "$HOOK")"
  RC=$?
}

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
    printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1))
    printf 'FAIL - %s\n' "$1"
  fi
}

# 1. Under budget on both arms → empty stdout, exit 0.
run_hook "$FIX/under.jsonl"
check "under-budget produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "under-budget exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 2. Over budget on the context-size arm → directive naming /handoff, exit 0.
run_hook "$FIX/over-ctx.jsonl"
check "over-budget (context arm) emits /handoff directive" \
  "$([ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '/handoff' && echo 0 || echo 1)"

# 3. Over budget on the re-prime arm (3 cache-creation spikes past the first
#    call) → directive naming /handoff, exit 0.
run_hook "$FIX/over-reprime.jsonl"
check "over-budget (re-prime arm) emits /handoff directive" \
  "$([ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '/handoff' && echo 0 || echo 1)"

# 4. Sidechain (subagent) usage is excluded from both arms — a huge
#    isSidechain:true entry after the real last main-loop call must not
#    surface in the computed context size or re-prime count.
run_hook "$FIX/sidechain-ignored.jsonl"
check "sidechain usage excluded produces empty stdout" \
  "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "sidechain usage excluded exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 5. A malformed/truncated trailing line (the transcript mid-write when the
#    hook fires) must not blank out the whole read — the valid lines before
#    it still drive the over-ctx directive.
run_hook "$FIX/truncated-tail.jsonl"
check "truncated trailing line still emits /handoff directive from prior valid lines" \
  "$([ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '/handoff' && echo 0 || echo 1)"

# 6. transcript_path absent from the stdin payload → silent no-op.
OUT="$(printf '{"session_id":"test-session","hook_event_name":"UserPromptSubmit","prompt":"go"}' | bash "$HOOK")"
RC=$?
check "missing transcript_path produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "missing transcript_path exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 7. transcript_path points at a nonexistent file → silent no-op.
run_hook "/no/such/transcript-$$.jsonl"
check "unreadable transcript produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "unreadable transcript exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 8. jq absent from PATH → silent no-op. Uses an absolute bash path since a
#    restricted PATH must not block resolving the interpreter itself.
OUT="$(stdin_for "$FIX/under.jsonl" | PATH="/nonexistent" /bin/bash "$HOOK")"
RC=$?
check "missing jq produces empty stdout" "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "missing jq exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 9. Custom budgets are honored: a session under the default 250000-token
#    ctx budget trips a lowered REFRESH_CTX_BUDGET.
run_hook "$FIX/under.jsonl" REFRESH_CTX_BUDGET=1000
check "lowered ctx budget trips the directive on an otherwise under-budget session" \
  "$([ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '/handoff' && echo 0 || echo 1)"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
