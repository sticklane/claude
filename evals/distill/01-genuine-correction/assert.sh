#!/usr/bin/env bash
# Grades the happy-path /distill run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed.
#
# The planted transcript records a genuine, non-obvious correction — the
# integration suite must be invoked as `./run-tests.sh --db=memory` or it
# hangs. A competent /distill captures this durable command gotcha into a
# doctrine file (its step-2 routing table). This grader asserts STRUCTURE:
# the literal flag `--db=memory` appears in at least one written doctrine
# file (CLAUDE.md, a rule, a docs/memory topic, or a new skill) — never the
# transcript itself, which is the harvest INPUT, not an output. It asserts
# capture, not any exact prose.
# bash 3.2 compatible: no `declare -A`, no bash-4+ syntax.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob

# Doctrine destinations /distill routes findings to. session-context.md is
# deliberately NOT in this set: matching the input would not prove capture.
doctrine=()
[ -f CLAUDE.md ] && doctrine+=(CLAUDE.md)
for f in .claude/rules/*.md; do doctrine+=("$f"); done
[ -f docs/memory.md ] && doctrine+=(docs/memory.md)
for f in docs/memory/*.md; do doctrine+=("$f"); done
for f in .claude/skills/*/SKILL.md; do doctrine+=("$f"); done

[ "${#doctrine[@]}" -gt 0 ] || fail "no doctrine files present — /distill captured nothing"

grep -qF -e '--db=memory' "${doctrine[@]}" \
  || fail "durable correction (--db=memory) not captured in any doctrine file"

echo "assert: durable correction captured into a doctrine file"
