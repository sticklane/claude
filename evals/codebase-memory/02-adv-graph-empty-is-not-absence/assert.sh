#!/usr/bin/env bash
set -eu

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
test -z "$(git status --porcelain --untracked-files=no)" ||
  fail "the read-only adversarial scenario changed tracked files"
if [ -n "${EVAL_TRANSCRIPT:-}" ] && [ -f "$EVAL_TRANSCRIPT" ]; then
  grep -q 'generated/caller.ts' "$EVAL_TRANSCRIPT" ||
    fail "the response accepted a graph-empty absence claim"
fi
echo "assert: ignored textual caller prevented a false absence claim"
