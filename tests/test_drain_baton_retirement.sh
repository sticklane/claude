#!/usr/bin/env bash
# The drain "count-based baton" wake-cost gap (specs/archive/drain-wake-cost)
# is structurally gone after the drain-to-Workflow pivot. These tests pin the
# three facts that keep the live docs honest about it:
#   1. drain's skill text still states no baton/lease/generation mechanism
#      exists (the structural fact the retirement rests on);
#   2. the archived spec is marked superseded, so every citation that lands
#      there reads as history rather than open work;
#   3. token-discipline records the residual risk that survives the pivot —
#      the orchestrator's own context still grows across collected verdicts.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SPEC="$TOOLKIT_DIR/specs/archive/drain-wake-cost/SPEC.md"
RULE="$TOOLKIT_DIR/.claude/rules/token-discipline.md"
DRAIN="$TOOLKIT_DIR/.claude/skills/drain/SKILL.md"

pass=0
fail=0

assert() { # assert <desc> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then pass=$((pass+1)); else
    fail=$((fail+1)); echo "FAIL: $desc" >&2; fi
}

assert "drain skill states no baton/lease/generation mechanism exists" \
  grep -qF 'no baton files, no lease files, no' "$DRAIN"

assert "drain skill loops on collected verdicts, not a generation boundary" \
  grep -qF 'Re-read `bd ready` after each collected verdict' "$DRAIN"

assert "archived wake-cost spec is marked superseded, not open" \
  grep -qE '^Status: superseded$' "$SPEC"

assert "archived wake-cost spec names what superseded it" \
  grep -qF 'Superseded-by:' "$SPEC"

assert "archived wake-cost spec is not still advertised as open" \
  test "$(grep -c '^Status: open$' "$SPEC")" -eq 0

assert "token-discipline records drain's residual context accumulation" \
  grep -qF 'residual accumulation' "$RULE"

echo "test_drain_baton_retirement: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
