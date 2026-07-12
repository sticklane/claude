#!/usr/bin/env bash
# Grades the /critique run. CWD is $EVAL_DIR; exit 0 = pass, non-zero with
# output explaining what failed.
#
# Critique's only documented artifact mutation (SKILL.md step 3) is the
# `Breakdown-ready: true` header, written on a READY verdict for a SPEC.md
# target and never written (or removed if stale) on NOT READY. This fixture
# is deliberately unambiguous (two independent, fully-specified,
# runnable-acceptance-criteria requirements) so a competent critic should
# reach READY — giving this artifact-only grader (v1 grades artifacts, not
# trajectory) a positive signal to check rather than only an absence.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

spec=specs/demo/SPEC.md
[ -f "$spec" ] || fail "$spec is missing"

head -n 5 "$spec" | grep -q '^Breakdown-ready: true' \
  || fail "$spec has no Breakdown-ready: true header near the top — critique did not mark this clean spec READY"

echo "assert: all checks passed (spec marked Breakdown-ready: true)"
