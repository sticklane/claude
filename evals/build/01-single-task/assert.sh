#!/usr/bin/env bash
# Grades the /build run. CWD is $EVAL_DIR; exit 0 = pass, non-zero with
# output explaining what failed. Artifact-only checks (no session.log
# reads — evals grade what a run produced, not its trajectory):
#   1. the task file ended Status: done;
#   2. the acceptance command it promised actually passes;
#   3. a commit landed beyond the fixture's own base commit.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

t=specs/demo/tasks/01-double-script.md
[ -f "$t" ] || fail "$t is missing"
grep -q '^Status: done' "$t" || fail "$t did not end Status: done"

test -x src/double.sh || fail "src/double.sh was not created executable"
out="$(./src/double.sh 21 2>/dev/null || true)"
[ "$out" = 42 ] || fail "./src/double.sh 21 printed '$out', expected 42"

base=$(git rev-list --max-parents=0 HEAD | head -1)
[ "$(git rev-parse HEAD)" != "$base" ] || fail "no commit landed beyond the fixture's base commit"

echo "assert: all checks passed (task done, acceptance command passes, commit landed)"
