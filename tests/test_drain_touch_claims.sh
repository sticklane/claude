#!/usr/bin/env bash
# Regression test for drain's Touch-overlap safety claims (bd issue agentic-8vf).
#
# drain/SKILL.md's step-2 concurrency-window guidance asserted that `bd ready`
# "already excludes file-overlapping work". No such logic exists in bd: the
# Touch-disjoint frontier lives in agentic/ready.py + agentic/frontier.py and
# is reached only through `python3 -m agentic ready`, which drain deliberately
# does not call (the 2026-07-23 cutover put grouping judgment in Claude's
# hands). Step 1 already documents this correctly, so the two steps
# contradicted each other and a concurrent window read off raw `bd ready`
# could dispatch colliding issues.
#
# The invariant: drain's skill files never attribute file/Touch-overlap
# exclusion to bd, and step 2's concurrency window attributes disjointness to
# the same Claude-side check step 1 describes.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$TOOLKIT_DIR/.claude/skills/drain/SKILL.md"
REFERENCE="$TOOLKIT_DIR/.claude/skills/drain/reference.md"

# Claims that would attribute Touch/file-overlap exclusion to bd itself.
FALSE_CLAIM_RE='bd computes this|bd ready.*excludes.*overlap|already excludes file-overlapping'

pass=0
fail=0

check() { # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

check "drain SKILL.md exists" test -f "$SKILL"
check "drain reference.md exists" test -f "$REFERENCE"

no_false_claim() { # no_false_claim <file>
  ! grep -qE "$FALSE_CLAIM_RE" "$1"
}

check "SKILL.md attributes no overlap-exclusion to bd" no_false_claim "$SKILL"
check "reference.md attributes no overlap-exclusion to bd" no_false_claim "$REFERENCE"

# Step 1's accurate caveat is the anchor step 2 must stay consistent with.
check "step 1 keeps its accurate 'bd does NOT compute file overlap' caveat" \
  grep -q 'bd does NOT compute file' "$SKILL"

# Extract the step-2 block (claim + dispatch) by structure, not a file-wide
# literal, so an unrelated mention elsewhere cannot satisfy the check.
step2="$(awk '/^2\. \*\*Claim, then dispatch/,/^3\. \*\*/' "$SKILL")"

check "step 2 block was located" test -n "$step2"

check "step 2's concurrency window cites the Touch-disjointness check" \
  grep -qiE 'touch[ -]disjoint' <<<"$step2"

check "step 2 makes no bd-does-the-overlap-check claim" \
  bash -c '! grep -qE "$1" <<<"$2"' _ "$FALSE_CLAIM_RE" "$step2"

echo "test_drain_touch_claims.sh: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]
