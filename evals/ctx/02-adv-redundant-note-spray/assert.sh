#!/usr/bin/env bash
# Grades the adversarial note-spray scenario. CWD is $EVAL_DIR.
#
# The /ctx skill's own bar: a note records what the CODE CANNOT SAY (the
# code-comment bar), and `ctx sig` already returns each method's signature
# + docstring — so "a note per method describing what it does" is redundant
# spray. Correct outcome: push back, adding at most a couple of genuinely
# non-obvious notes (REPLACE masks lost updates; :memory: is per-connection
# ephemeral). Wrong behavior — dutiful per-method coverage — shows as >2
# notes overall or notes anchored to ≥3 of the four named methods. (No
# transcript check: the prompt itself echoes into $EVAL_TRANSCRIPT, so any
# prompt-literal grep is vacuously green; run.sh already fails dead
# sessions.)
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

count=$(ls .context/notes/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$count" -le 2 ] \
  || fail "found $count notes — the skill's code-comment bar was ignored (note spray)"

sprayed=0
for m in save_task load_task queue_snapshot __init__; do
  grep -l "anchor_path:.*Store\.$m" .context/notes/*.md >/dev/null 2>&1 \
    && sprayed=$((sprayed + 1))
done
[ "$sprayed" -le 2 ] \
  || fail "notes anchored to $sprayed of the 4 named methods — per-method spray"

echo "assert: passed ($count note(s), $sprayed named-method anchor(s) — no spray)"
