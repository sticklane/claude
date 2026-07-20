#!/usr/bin/env bash
# Grades the /prioritize happy-path run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed.
#
# A correct run rewrites exactly the two named Priority headers (alpha/01 ->
# P0, beta/01 -> P3) and commits per R6; the unnamed distractor task must
# keep its P2 (the skill touches only named files).
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

grep -q '^Priority: P0' specs/alpha/tasks/01-parser.md \
  || fail "alpha/01-parser.md Priority was not rewritten to P0"
grep -q '^Priority: P3' specs/beta/tasks/01-loader.md \
  || fail "beta/01-loader.md Priority was not rewritten to P3"
grep -q '^Priority: P2' specs/alpha/tasks/02-formatter.md \
  || fail "alpha/02-formatter.md Priority changed — skill touched an unnamed task"

git log --format=%s | grep -q '^chore: reprioritize' \
  || fail "no 'chore: reprioritize' commit found — R6 commit did not fire"

echo "assert: all checks passed (two headers rewritten, distractor intact, commit made)"
