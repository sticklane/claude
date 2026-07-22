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
#
# Both markers are scoped to the Acceptance section body ($accept), not the
# whole spec file: /idea records the "verified <date>" note and the
# `Depth ceiling:` line inline with the criterion they annotate (SKILL.md
# step 3 + step 4), so a marker that appears only in Problem/Requirements
# elsewhere in the file does not anchor the acceptance criterion under test.
# File-wide greps let an unanchored grep criterion pass whenever those strings
# happened to appear anywhere else in the spec.
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
  # criterion but records no "verified <date>" anchor note in the Acceptance
  # section (a note elsewhere in the file does not anchor this criterion).
  printf '%s\n' "$accept" | grep -Eqi 'verified[[:space:]]+[0-9]{4}-[0-9]{2}-[0-9]{2}' \
    || fail "keeps a grep acceptance criterion but records no 'verified <date>' anchor note in the Acceptance section (unanchored grep criterion)"

  # Anti-pattern 2 — self-referential doctrine-word grep with no depth
  # ceiling: the L0 grep is not legalized by a 'Depth ceiling:' annotation
  # in the Acceptance section (an annotation elsewhere does not legalize it).
  printf '%s\n' "$accept" | grep -Eqi '^[[:space:]]*Depth ceiling:' \
    || fail "keeps a doctrine-word grep criterion but carries no 'Depth ceiling:' annotation in the Acceptance section naming a behavioral complement"
fi

echo "assert: all checks passed (no unanchored or unceilinged doctrine-word grep criterion)"
