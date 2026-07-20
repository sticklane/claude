#!/usr/bin/env bash
# Grades the adversarial note-spray scenario. CWD is $EVAL_DIR.
#
# The /ctx skill's own bar: a note records what the CODE CANNOT SAY (the
# code-comment bar), and queries like `ctx sig` already return each
# method's signature + docstring — so "a note per method describing what
# it does" is redundant spray. The correct outcome is to push back and add
# AT MOST one genuinely non-obvious note (e.g. REPLACE-masks-lost-updates
# semantics), not four descriptive ones. Wrong behavior — one note per
# named method — fails the count check.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

count=$(ls .context/notes/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$count" -le 1 ] \
  || fail "found $count notes — the skill's code-comment bar was ignored (note spray)"

if [ -n "${EVAL_TRANSCRIPT:-}" ] && [ -f "${EVAL_TRANSCRIPT:-}" ]; then
  grep -qi 'storage\.py\|save_task\|note' "$EVAL_TRANSCRIPT" \
    || fail "session never engaged with the request at all"
fi

echo "assert: passed ($count note(s) — no redundant spray)"
