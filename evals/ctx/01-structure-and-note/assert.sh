#!/usr/bin/env bash
# Grades the /ctx happy path. CWD is $EVAL_DIR; exit 0 = pass.
#
# A correct run answers the structure question (def in dispatch.py, ref in
# api.py) and records an invariant note anchored to claim_next via ctx —
# the note must exist in .context/notes/, be anchored to the claim_next
# symbol, carry kind=invariant, and read back fresh through the binary.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
CTX=./context-tree/target/release/ctx

ls .context/notes/*.md >/dev/null 2>&1 \
  || fail "no note file under .context/notes/ — the note was never recorded"

out="$("$CTX" notes pyserver.taskflow.dispatch.Dispatcher.claim_next 2>&1)"
echo "$out" | grep -q 'kind=invariant' \
  || fail "no invariant-kind note anchored to claim_next (got: $out)"
echo "$out" | grep -qi 'attempts' \
  || fail "note text does not mention the attempts accounting (got: $out)"
echo "$out" | grep -q 'fresh' \
  || fail "note is not fresh against the current tree (got: $out)"

if [ -n "${EVAL_TRANSCRIPT:-}" ] && [ -f "${EVAL_TRANSCRIPT:-}" ]; then
  grep -q 'dispatch\.py' "$EVAL_TRANSCRIPT" \
    || fail "session never surfaced dispatch.py — structure question unanswered"
fi

echo "assert: all checks passed (anchored invariant note + structure answer)"
