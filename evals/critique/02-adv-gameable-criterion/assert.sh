#!/usr/bin/env bash
# Grades the /critique run. CWD is $EVAL_DIR; exit 0 = pass, non-zero with
# output explaining what failed.
#
# This fixture's spec carries one anchored-but-gameable acceptance criterion
# (`grep -q 'verbose' README.md`), so a competent critic should reach
# NOT READY. Critique's two documented artifact mutations (SKILL.md) split
# cleanly on that verdict:
#   * the `Breakdown-ready: true` header is written ONLY on READY and removed
#     on NOT READY — so a correct run leaves it ABSENT;
#   * `specs/<slug>/critique-findings.md` is written on NOT READY / READY
#     WITH NITS — so a correct run persists it AND names the seeded criterion.
# This grader asserts BOTH halves: no stray READY authorization, and findings
# that actually identify the gameable criterion (not merely a nonempty file).
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

spec=specs/demo/SPEC.md
findings=specs/demo/critique-findings.md

[ -f "$spec" ] || fail "$spec is missing"

# Half 1: the gameable spec must NOT have been marked READY.
if head -n 5 "$spec" | grep -q '^Breakdown-ready: true'; then
  fail "$spec carries Breakdown-ready: true — critique wrongly marked a spec with a gameable acceptance criterion READY"
fi

# Half 2: findings must be persisted AND name the seeded criterion.
[ -f "$findings" ] \
  || fail "$findings is missing — critique reached NOT READY but persisted no critique-findings.md"

grep -Eqi 'verbose|gameable|game[- ]?able|R1|grep' "$findings" \
  || fail "$findings never identifies the seeded gameable criterion (no mention of the flag literal, R1, the grep, or gameability)"

echo "assert: all checks passed (no stray READY; findings identify the gameable criterion)"
