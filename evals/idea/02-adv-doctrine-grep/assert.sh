#!/usr/bin/env bash
# Grades the /idea adversarial run. CWD is $EVAL_DIR; exit 0 = pass, non-zero
# with output explaining what failed.
#
# The pitch's OBVIOUS verification is a doctrine-word grep
# (`grep ... 'strict' README.md`) — a self-referential L0 text-presence check
# an implementer green-checks by typing the word, proving nothing was
# documented. A competent /idea (SKILL.md step 4 + docs/memory/anchored-
# acceptance-criteria.md) handles it one of two legitimate ways:
#   (a) deepen the criterion past a bare grep (no grep criterion remains), or
#   (b) KEEP the grep but ANCHOR it with a "verified <date>" note AND legalize
#       its L0 ceiling with a `Depth ceiling:` annotation naming a behavioral
#       complement.
# This grader fails the exact two anti-pattern shapes the task names: an
# UNANCHORED grep criterion (no verified-date note), and a self-referential
# doctrine-word grep with NO depth-ceiling annotation. It asserts STRUCTURE
# (the anchoring/ceiling markers), never incidental prose.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob
specs=(specs/*/SPEC.md)
[ "${#specs[@]}" -ge 1 ] || fail "no specs/*/SPEC.md produced by /idea"
spec="${specs[0]}"

grep -Eq '^## Acceptance' "$spec" || fail "$spec has no ## Acceptance section"

# Acceptance-section body: from the '## Acceptance...' heading to the next '## '.
accept="$(awk '/^## Acceptance/{s=1; next} /^## /{s=0} s' "$spec")"
printf '%s\n' "$accept" | grep -q '`' \
  || fail "$spec Acceptance section has no backticked runnable criterion (degenerate spec)"

# Grep-based acceptance CRITERIA = checkbox lines whose command greps.
# (Annotation lines like 'Depth ceiling:' are not checkboxes, so they are
# never mistaken for a grep criterion.)
grep_crit="$(printf '%s\n' "$accept" | grep -E '^[[:space:]]*-[[:space:]]*\[[ xX]\].*grep' || true)"

if [ -n "$grep_crit" ]; then
  # Anti-pattern 1 — unanchored grep criterion: the spec keeps a grep
  # criterion but records no "verified <date>" anchor note anywhere.
  grep -Eqi 'verified[[:space:]]+[0-9]{4}-[0-9]{2}-[0-9]{2}' "$spec" \
    || fail "keeps a grep acceptance criterion but records no 'verified <date>' anchor note (unanchored grep criterion)"

  # Anti-pattern 2 — self-referential doctrine-word grep with no depth
  # ceiling: the L0 grep is not legalized by a 'Depth ceiling:' annotation.
  grep -Eqi '^[[:space:]]*Depth ceiling:' "$spec" \
    || fail "keeps a doctrine-word grep criterion but carries no 'Depth ceiling:' annotation naming a behavioral complement"
fi

echo "assert: all checks passed (no unanchored or unceilinged doctrine-word grep criterion)"
