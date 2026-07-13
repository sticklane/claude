#!/usr/bin/env bash
# Unit tests for refresh-check.sh — the session-refresh prompt-submit hook.
# Drives the hook against synthetic agentprof summary fixtures via a fake
# agentprof double, asserting the over-budget directive appears on exactly
# the over-budget path and nowhere else. Never touches real session data.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/refresh-check.sh"
FIX="$DIR/fixtures"
FAKE="$FIX/fake-agentprof.sh"

pass=0
fail=0

# stdin_for <session-id> — a synthetic UserPromptSubmit hook payload.
stdin_for() {
  printf '{"session_id":"%s","hook_event_name":"UserPromptSubmit","prompt":"go"}' "$1"
}

# run_with_fake <fixture-basename> <session-id> — invoke the hook with the
# fake agentprof wired in, capturing stdout. Sets OUT and RC.
run_with_fake() {
  local fixture="$FIX/$1" sid="$2"
  OUT="$(stdin_for "$sid" | AGENTPROF_BIN="$FAKE" FAKE_SUMMARY_SRC="$fixture" \
    bash "$HOOK")"
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

# 1. Over budget on the re-prime arm → directive naming /handoff, exit 0.
run_with_fake over-reprime.json test-session
check "over-budget (re-prime arm) emits /handoff directive" \
  "$([ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '/handoff' && echo 0 || echo 1)"

# 2. Over budget on the context arm → directive naming /handoff, exit 0.
run_with_fake over-ctx.json test-session
check "over-budget (context arm) emits /handoff directive" \
  "$([ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '/handoff' && echo 0 || echo 1)"

# 3. Under budget → zero bytes on stdout, exit 0. (The fixture also holds a
#    separate over-budget session, proving the hook reads only its own id.)
run_with_fake under.json test-session
check "under-budget produces empty stdout" \
  "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "under-budget exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 4. Session id absent from the summary → treated as under budget (empty).
run_with_fake under.json ghost-session
check "session absent from summary produces empty stdout" \
  "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "session absent from summary exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 5. agentprof binary absent from PATH → empty stdout, exit 0. A committed
#    fake-jq fixture stands in as `jq` (first on the restricted PATH) so the
#    hook clears its `command -v jq` guard on ANY machine — real jq may live
#    outside /usr/bin:/bin (e.g. homebrew's /opt/homebrew/bin) — and so
#    reaches the intended agentprof-binary-absent branch instead of
#    short-circuiting at the jq guard. agentprof itself stays unresolvable on
#    the restricted PATH. The setup (fixture present + executable) is gated
#    into the assertion, so a missing/unusable fixture fails test 5 rather
#    than silently falling through to a system jq.
JQBIN="$(mktemp -d)"
cp "$FIX/fake-jq.sh" "$JQBIN/jq" && chmod +x "$JQBIN/jq"
JQ_SETUP=$?
OUT="$(stdin_for test-session | env -u AGENTPROF_BIN PATH="$JQBIN:/usr/bin:/bin" \
  bash "$HOOK")"
RC=$?
rm -rf "$JQBIN"
check "missing agentprof binary produces empty stdout" \
  "$([ "$JQ_SETUP" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"
check "missing agentprof binary exits 0" \
  "$([ "$JQ_SETUP" -eq 0 ] && [ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 6. agentprof present but erroring → empty stdout, exit 0.
OUT="$(stdin_for test-session | AGENTPROF_BIN="$FAKE" FAKE_AGENTPROF_FAIL=1 \
  bash "$HOOK")"
RC=$?
check "agentprof error produces empty stdout" \
  "$([ -z "$OUT" ] && echo 0 || echo 1)"
check "agentprof error exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
