#!/usr/bin/env bash
# Grader for the NOW.md focus selector and its dependency-closure scope.
#
# What it proves:
#   1. a bare drain selects slug[0] of specs/NOW.md as the focus — feat-a's
#      issue lands.
#   2. the focus scope is the transitive closure of blocking dependencies —
#      the imported feat-c blocker lands even though no NOW.md entry names it.
#   3. the scope stops there — feat-b's ready issue is untouched and still
#      open, so drain did not silently widen to the whole queue.
#   4. the imported work is reported as imported, naming its donor slug.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
command -v bd >/dev/null 2>&1 || fail "bd not on PATH (bd is the source of truth after the cutover)"
[ -f .eval-focus-seed ] || fail "fixture seed .eval-focus-seed is missing; run setup.sh first"

read -r IMPORTED FOCUS OFFFOCUS < .eval-focus-seed
[ -n "$IMPORTED" ] && [ -n "$FOCUS" ] && [ -n "$OFFFOCUS" ] ||
  fail "fixture seed ids are incomplete"

status_of() {
  bd show "$1" --json 2>/dev/null |
    python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["status"])'
}
hex_of() { od -An -t x1 "$1" 2>/dev/null | tr -d ' \n'; }

[ "$(status_of "$FOCUS")" = closed ] || fail "the top NOW.md slug's issue was not closed"
[ "$(hex_of focus.txt)" = 666f6375730a ] || fail "focus.txt artifact is missing or wrong"

[ "$(status_of "$IMPORTED")" = closed ] ||
  fail "the imported blocker was not closed — the focus closure did not import it"
[ "$(hex_of imported.txt)" = 696d706f727465640a ] ||
  fail "imported.txt artifact is missing or wrong"

[ "$(status_of "$OFFFOCUS")" = closed ] &&
  fail "the second NOW.md slug's issue was closed — the run was not focus-scoped"
[ -e offfocus.txt ] && fail "offfocus.txt exists — out-of-focus work was implemented"

ready="$(bd ready --json 2>/dev/null | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
[ "$ready" -ge 1 ] || fail "no ready work remains; the run drained past its focus"

[ -s session.log ] || fail "session.log is missing"
grep -q 'DRAIN_EVAL_COMPLETE' session.log || fail "the run did not report focus-drain completion"
grep -qi 'imported blocking work' session.log ||
  fail "session never reported the imported blocker under 'imported blocking work'"
grep -q 'feat-c' session.log ||
  fail "session never named the donor slug of the imported blocking work"

echo "assert: focus selection OK (slug[0] plus its imported blocking closure landed, feat-b untouched)"
