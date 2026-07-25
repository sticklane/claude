#!/usr/bin/env bash
# The drain "count-based baton" wake-cost gap (specs/archive/drain-wake-cost)
# is structurally gone after the drain-to-Workflow pivot. These tests pin the
# three facts that keep the live docs honest about it:
#   1. drain's skill text still states no baton/lease/generation mechanism
#      exists (the structural fact the retirement rests on);
#   2. the archived spec is marked superseded, so every citation that lands
#      there reads as history rather than open work;
#   3. token-discipline records the residual risk that survives the pivot —
#      the orchestrator's own context still grows across collected verdicts;
#   4. no mechanism word (baton, lease file, generation counter) appears in
#      drain's skill files outside the sentences that disclaim it — the
#      canary that goes red if the mechanism is ever re-added.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SPEC="$TOOLKIT_DIR/specs/archive/drain-wake-cost/SPEC.md"
RULE="$TOOLKIT_DIR/.claude/rules/token-discipline.md"
DRAIN="$TOOLKIT_DIR/.claude/skills/drain/SKILL.md"
DRAIN_REF="$TOOLKIT_DIR/.claude/skills/drain/reference.md"

pass=0
fail=0

assert() { # assert <desc> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then pass=$((pass+1)); else
    fail=$((fail+1)); echo "FAIL: $desc" >&2; fi
}

refute() { # refute <desc> <command...> — passes when the command FAILS
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail+1)); echo "FAIL: $desc" >&2; else pass=$((pass+1)); fi
}

# Prints every mechanism word left in a drain skill file once the two
# sentences that disclaim the mechanism are removed. Any output means drain
# talks about a baton, lease file, or generation counter somewhere other than
# to deny having one — i.e. the retired mechanism is back.
mechanism_mentions_outside_disclaimer() { # <file>
  tr '\n' ' ' <"$1" | tr -s ' ' \
    | sed -e 's/There are no baton files, no lease files, no generation counters, and no drain-owned handoff files//g' \
          -e 's|The old baton/lease/generation/tournament/swarm apparatus is deleted||g' \
    | grep -oiE 'baton|lease file|generation counter'
}

assert "drain skill states no baton/lease/generation mechanism exists" \
  grep -qF 'no baton files, no lease files, no' "$DRAIN"

assert "drain skill loops on collected verdicts, not a generation boundary" \
  grep -qF 'Re-read `bd ready` after each collected verdict' "$DRAIN"

refute "drain SKILL.md mentions no mechanism outside its disclaiming sentence" \
  mechanism_mentions_outside_disclaimer "$DRAIN"

refute "drain reference.md mentions no mechanism outside its disclaiming sentence" \
  mechanism_mentions_outside_disclaimer "$DRAIN_REF"

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
