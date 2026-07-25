#!/usr/bin/env bash
# Bring the session-refresh hook's own suite inside scripts/check.sh, whose
# glob is tests/test_*.sh — without this the hook is ungated. Adds one
# regression case the hook suite's fixtures cannot express: a paired pair of
# transcripts identical except for isSidechain, proving the hook's sidechain
# exclusion is load-bearing rather than decorative.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$ROOT/hooks/session-refresh/refresh-check.sh"

command -v jq >/dev/null 2>&1 || {
  printf 'skip - sidechain regression needs jq\n'
  exec bash "$ROOT/hooks/session-refresh/test.sh"
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# assistant_line <isSidechain> — one usage entry whose context size (600000)
# is well past the 250000-token default budget.
assistant_line() {
  printf '{"type":"assistant","isSidechain":%s,"message":{"usage":{"input_tokens":100000,"cache_read_input_tokens":500000}}}\n' "$1"
}

main_only="$work/main-loop-small.jsonl"
printf '{"type":"assistant","isSidechain":false,"message":{"usage":{"input_tokens":10,"cache_read_input_tokens":20}}}\n' >"$main_only"

sidechain_big="$work/sidechain-big.jsonl"
cat "$main_only" >"$sidechain_big"
assistant_line true >>"$sidechain_big"

mainloop_big="$work/mainloop-big.jsonl"
cat "$main_only" >"$mainloop_big"
assistant_line false >>"$mainloop_big"

run_hook() {
  printf '{"session_id":"sidechain-regression","transcript_path":"%s","hook_event_name":"UserPromptSubmit","prompt":"go"}' "$1" |
    bash "$HOOK"
}

sidechain_out="$(run_hook "$sidechain_big")"
mainloop_out="$(run_hook "$mainloop_big")"

fail=0
if [ -n "$sidechain_out" ]; then
  printf 'FAIL - an over-budget sidechain entry must not trip the wake-budget directive\n'
  fail=1
else
  printf 'ok   - an over-budget sidechain entry does not trip the wake-budget directive\n'
fi

if printf '%s' "$mainloop_out" | grep -q '/handoff'; then
  printf 'ok   - the same over-budget entry on the main loop does trip the directive\n'
else
  printf 'FAIL - the same over-budget entry on the main loop must trip the directive\n'
  fail=1
fi

bash "$ROOT/hooks/session-refresh/test.sh" || fail=1

[ "$fail" -eq 0 ]
