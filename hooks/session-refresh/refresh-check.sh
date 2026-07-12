#!/usr/bin/env bash
# session-refresh: UserPromptSubmit hook that flags a session over its wake
# budget. On prompt-submit it reads the session id from the hook's stdin JSON,
# asks agentprof for that session's re-prime count and p90 main-loop context,
# and — past either arm of the R1 budget (.claude/rules/token-discipline.md,
# "Session refresh") — prints a directive telling the session to write a
# /handoff and end instead of carrying its fat context into another wake.
#
# agentprof is the single source of the re-prime definition: this hook never
# re-implements the parse-time rule, it shells out (spec R2/R2a). It is a
# silent no-op (empty stdout, exit 0) under budget, on any agentprof error,
# when the binary or jq is absent, and when the session is not yet in the
# summary — a missing profiler must never break a session's prompt.
#
# Budgets and the look-back window are tunable via environment (R1: defaults
# are the 30-day-profile pins, not hard limits):
#   REFRESH_REPRIME_BUDGET  re-prime count arm         (default 3)
#   REFRESH_CTX_BUDGET      p90 context-token arm      (default 250000)
#   REFRESH_SINCE_DAYS      agentprof --since look-back (default 2)
#   AGENTPROF_BIN           explicit agentprof path (else resolved on PATH)
set -u

REPRIME_BUDGET="${REFRESH_REPRIME_BUDGET:-3}"
CTX_BUDGET="${REFRESH_CTX_BUDGET:-250000}"
SINCE_DAYS="${REFRESH_SINCE_DAYS:-2}"

# jq parses both the stdin payload and the summary; without it, no-op.
command -v jq >/dev/null 2>&1 || exit 0

sid="$(jq -r '.session_id // empty' 2>/dev/null)"
[ -n "$sid" ] || exit 0

# Resolve agentprof: explicit override, else PATH. Absent → silent no-op.
bin="${AGENTPROF_BIN:-}"
[ -n "$bin" ] || bin="$(command -v agentprof 2>/dev/null || true)"
[ -n "$bin" ] && [ -x "$bin" ] || exit 0

# BSD `date -v` (macOS, matching agentprof/scripts/refresh-profile.sh); fall
# back to GNU `date -d` so the hook also works under a Linux harness.
since="$(date -u -v-"${SINCE_DAYS}"d '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null \
  || date -u -d "${SINCE_DAYS} days ago" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)"
[ -n "$since" ] || exit 0

summary="$(mktemp 2>/dev/null)" || exit 0
trap 'rm -f "$summary"' EXIT

# Single-session read per R2a: the full `--since` summary plus a jq filter on
# the session id. -o /dev/null discards the profile; we only want the summary.
"$bin" claude --since "$since" --summary "$summary" -o /dev/null \
  >/dev/null 2>&1 || exit 0
[ -s "$summary" ] || exit 0

reprime="$(jq -r --arg s "$sid" '.sessions[$s].reprime_count // 0' \
  "$summary" 2>/dev/null)" || exit 0
p90="$(jq -r --arg s "$sid" '.sessions[$s].p90_ctx // 0' \
  "$summary" 2>/dev/null)" || exit 0

# Guard against any non-integer jq result (malformed/older summary).
case "$reprime" in '' | *[!0-9]*) reprime=0 ;; esac
case "$p90" in '' | *[!0-9]*) p90=0 ;; esac

if [ "$reprime" -ge "$REPRIME_BUDGET" ] || [ "$p90" -ge "$CTX_BUDGET" ]; then
  cat <<EOF
Over wake budget: this session has re-primed the prompt cache ${reprime} time(s) and its p90 main-loop context is ${p90} tokens, past the refresh budget (${REPRIME_BUDGET} re-primes / ${CTX_BUDGET} tokens).
Write a handoff now with /handoff and end this session instead of continuing — refresh-over-carry. A fresh session resuming from the handoff avoids re-paying the accumulated context on every wake.
EOF
fi

exit 0
