#!/usr/bin/env bash
# Grades the /idea happy-path run. CWD is $EVAL_DIR; exit 0 = pass, non-zero
# with output explaining what failed.
#
# /idea CREATES the spec, so the fixture seeds none: any specs/*/SPEC.md is
# the produced artifact. Assert the TEMPLATE STRUCTURE (SKILL.md step 4) — the
# named sections plus at least one runnable, backticked acceptance criterion —
# never incidental wording or a specific slug.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob
specs=(specs/*/SPEC.md)
[ "${#specs[@]}" -ge 1 ] || fail "no specs/*/SPEC.md produced by /idea"

for spec in "${specs[@]}"; do
  grep -q '^## Problem'      "$spec" || fail "$spec has no ## Problem section"
  grep -q '^## Requirements' "$spec" || fail "$spec has no ## Requirements section"
  grep -Eq '^## Acceptance'  "$spec" || fail "$spec has no ## Acceptance section"

  # The Acceptance section must carry at least one runnable (backticked)
  # criterion — structure, not wording.
  awk '/^## Acceptance/{s=1; next} /^## /{s=0} s' "$spec" | grep -q '`' \
    || fail "$spec Acceptance section has no backticked runnable criterion"
done

echo "assert: all checks passed (${#specs[@]} spec(s): template sections + runnable criteria present)"
