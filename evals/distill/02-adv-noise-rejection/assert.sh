#!/usr/bin/env bash
# Grades the adversarial /distill run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed.
#
# The planted transcript carries BOTH a genuine durable convention
# (`LINT_STRICT=1 make lint`) and one-off noise (a throwaway scratch path
# /tmp/wt-zpopulk-7731). A competent /distill captures the first into a
# doctrine file and, per its routing gate, writes the second NOWHERE.
# This grader asserts STRUCTURE two ways:
#   (a) durable captured: the literal `LINT_STRICT` appears in a doctrine file;
#   (b) noise rejected: the sentinel `zpopulk-7731` appears in NO doctrine
#       file.
# Doctrine files only — session-context.md (the harvest INPUT) is excluded, so
# neither check ever matches the transcript. A do-nothing run fails (a); a run
# that hoards the noise fails (b).
# bash 3.2 compatible: no `declare -A`, no bash-4+ syntax.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob

doctrine=()
[ -f CLAUDE.md ] && doctrine+=(CLAUDE.md)
for f in .claude/rules/*.md; do doctrine+=("$f"); done
[ -f docs/memory.md ] && doctrine+=(docs/memory.md)
for f in docs/memory/*.md; do doctrine+=("$f"); done
for f in .claude/skills/*/SKILL.md; do doctrine+=("$f"); done

[ "${#doctrine[@]}" -gt 0 ] || fail "no doctrine files present — /distill captured nothing"

# (a) durable convention captured
grep -qF -e 'LINT_STRICT' "${doctrine[@]}" \
  || fail "durable convention (LINT_STRICT) not captured in any doctrine file"

# (b) one-off noise rejected — sentinel must appear in no doctrine file
if grep -qF -e 'zpopulk-7731' "${doctrine[@]}"; then
  fail "one-off noise (zpopulk-7731) leaked into a doctrine file"
fi

echo "assert: durable convention captured; one-off noise rejected"
