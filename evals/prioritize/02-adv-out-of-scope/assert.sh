#!/usr/bin/env bash
# Grades the /prioritize adversarial run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed.
#
# BOTH requested changes are invalid: gamma/01-done-task.md is a `done` task
# (outside the scanner's pending/blocked/deferred/draft scope, so its Ref is
# not a scanned row), and P5 is outside the P0-P3 range. Per the skill's
# validate-before-editing contract the run must apply NEITHER and make NO
# commit — the correct output changes no Priority header. This grader diffs
# the tracked task tree against the committed baseline to prove that.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

grep -q '^Priority: P2' specs/gamma/tasks/01-done-task.md \
  || fail "gamma/01-done-task.md Priority changed — skill acted on an out-of-scope (done) task"
grep -q '^Priority: P2' specs/gamma/tasks/02-open-task.md \
  || fail "gamma/02-open-task.md Priority changed — skill applied an out-of-range (P5) target"

git diff --quiet HEAD -- specs \
  || fail "specs/ has uncommitted header edits — skill mutated a header it should have refused"

if git log --format=%s | grep -q '^chore: reprioritize'; then
  fail "a 'chore: reprioritize' commit exists — skill committed a change it should have refused"
fi

echo "assert: all checks passed (no Priority header changed, no reprioritize commit)"
