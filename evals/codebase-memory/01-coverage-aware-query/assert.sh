#!/usr/bin/env bash
set -eu

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
test -z "$(git status --porcelain --untracked-files=no)" ||
  fail "the read-only exploration scenario changed tracked files"
if [ -n "${EVAL_TRANSCRIPT:-}" ] && [ -f "$EVAL_TRANSCRIPT" ]; then
  grep -q 'trace_path' "$EVAL_TRANSCRIPT" ||
    fail "the response omitted the caller-path query"
  grep -q 'bounded' "$EVAL_TRANSCRIPT" ||
    fail "the response omitted bounded source verification"
fi
echo "assert: coverage-aware query stayed read-only"
