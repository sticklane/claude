#!/usr/bin/env bash
# Grades the /breakdown run. CWD is $EVAL_DIR; exit 0 = pass, non-zero
# with output explaining what failed.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob
tasks=(specs/demo/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -ge 2 ] || fail "expected >=2 specs/demo/tasks/NN-*.md files, found ${#tasks[@]}"

for t in "${tasks[@]}"; do
  grep -q "^Status:" "$t" || fail "$t has no Status: line"
  grep -q "^Depends on:" "$t" || fail "$t has no Depends on: line"
  grep -q "^## Acceptance" "$t" || fail "$t has no ## Acceptance section"
  awk '/^## Acceptance/{in_sec=1; next} /^## /{in_sec=0} in_sec' "$t" | grep -q '`' \
    || fail "$t Acceptance section has no backticked command"
done

grep -q "Parallelization" specs/demo/SPEC.md \
  || fail "specs/demo/SPEC.md gained no Parallelization section"

echo "assert: all checks passed (${#tasks[@]} task files)"
