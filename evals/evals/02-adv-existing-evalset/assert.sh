#!/usr/bin/env bash
# Grades the adversarial /evals run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed.
#
# The greet skill already has an evalset (evals/greet/01-hello/), so /evals
# must NOT scaffold over it (step 1 scaffolds only "If evals/<skill>/ has no
# scenario"). A correct run leaves the seeded scenario intact:
#   1. exactly one scenario dir under evals/greet/ (no second one scaffolded);
#   2. the seeded files are byte-unchanged (git-tracked, committed by setup);
#   3. the sentinel survives in the seeded assert.sh.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob
scenarios=(evals/greet/[0-9][0-9]-*/)
[ "${#scenarios[@]}" -eq 1 ] \
  || fail "expected exactly 1 evals/greet scenario dir, found ${#scenarios[@]} — /evals scaffolded over an existing evalset"

git diff --quiet HEAD -- evals/greet/ \
  || fail "/evals modified the existing evalset's committed files — it must not scaffold over an existing evalset"

grep -q 'ADV_SENTINEL_DO_NOT_OVERWRITE' evals/greet/01-hello/assert.sh \
  || fail "sentinel gone from evals/greet/01-hello/assert.sh — the seeded grader was clobbered"

echo "assert: all checks passed (existing evalset untouched — /evals did not scaffold over it)"
