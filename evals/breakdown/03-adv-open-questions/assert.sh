#!/usr/bin/env bash
# Grades the adversarial /breakdown run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed.
#
# The fixture spec has UNRESOLVED "## Open questions", so /breakdown must
# REFUSE to decompose it. A correct run leaves NO evidence of decomposition:
#   1. no specs/demo/tasks/NN-*.md task files were created;
#   2. SPEC.md gained no "## Parallelization" section.
# This grader fails loudly if the skill DID act on input it must refuse.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

[ -f specs/demo/SPEC.md ] || fail "specs/demo/SPEC.md is missing"

shopt -s nullglob
tasks=(specs/demo/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -eq 0 ] \
  || fail "breakdown created ${#tasks[@]} task file(s) for a spec with unresolved open questions — it must refuse to decompose"

if grep -q '^## Parallelization' specs/demo/SPEC.md; then
  fail "breakdown added a ## Parallelization section to a spec it must refuse to decompose"
fi

echo "assert: all checks passed (no tasks created, no Parallelization section — breakdown refused the ambiguous spec)"
