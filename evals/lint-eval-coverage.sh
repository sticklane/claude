#!/usr/bin/env bash
# lint-eval-coverage.sh — model-free check that the repo satisfies its own
# eval-coverage policy in evals/COVERAGE.md. Enforces R2's five violation
# classes and exits 0 only on a conforming tree, listing each violation
# it finds. Invoked directly, never wired into evals/run.sh (that runs paid
# model sessions). Ref: specs/eval-coverage-tiers/SPEC.md R1, R2.
#
# Root override for the self-test (tests/test_eval_coverage_lint.sh):
#   LINT_ROOT=<dir> repoints every path below at a throwaway fixture tree.
#
# The five violation classes, each printed with a stable, greppable tag:
#   no-coverage-row: <skill>              a [!_]* skill dir with no table row
#   tier-a-too-few-scenarios: <skill>     Tier A with < 2 conforming scenarios
#   tier-a-no-adversarial: <skill>        Tier A with no NN-adv-* scenario
#   tier-b-missing-test: <skill> -> <p>   Tier B row names an absent test file
#   tier-c-empty-reason: <skill>          Tier C row with an empty reason
# A conforming scenario dir contains setup.sh + prompt.txt + assert.sh.
set -u
shopt -s nullglob

ROOT="${LINT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SKILLS_DIR="$ROOT/.claude/skills"
EVALS_DIR="$ROOT/evals"
COVERAGE="$EVALS_DIR/COVERAGE.md"

violations=0
report() { echo "$1"; violations=$((violations + 1)); }

if [ ! -f "$COVERAGE" ]; then
  echo "lint-eval-coverage: FAIL — coverage file missing: $COVERAGE"
  exit 1
fi

# Parse COVERAGE.md's markdown table. A data row is a 4-column table line
# (| skill | tier | reason | tests |) whose tier cell is exactly A, B, or C;
# the header and separator rows fail that test and are skipped without
# hard-coding their text.
declare -A TIER REASON TESTS
while IFS=$'\t' read -r skill tier reason tests; do
  [ -n "$skill" ] || continue
  TIER["$skill"]="$tier"
  REASON["$skill"]="$reason"
  TESTS["$skill"]="$tests"
done < <(awk -F'|' '
  NF >= 6 {
    s = $2; t = $3; r = $4; tf = $5
    gsub(/^[ \t]+|[ \t]+$/, "", s)
    gsub(/^[ \t]+|[ \t]+$/, "", t)
    gsub(/^[ \t]+|[ \t]+$/, "", r)
    gsub(/^[ \t]+|[ \t]+$/, "", tf)
    if (t == "A" || t == "B" || t == "C")
      printf "%s\t%s\t%s\t%s\n", s, t, r, tf
  }
' "$COVERAGE")

check_tier_a() {
  local skill="$1" sdir="$EVALS_DIR/$1" count=0 has_adv=0 sc name
  for sc in "$sdir"/*/; do
    name="$(basename "$sc")"
    if [ -f "$sc/setup.sh" ] && [ -f "$sc/prompt.txt" ] && [ -f "$sc/assert.sh" ]; then
      count=$((count + 1))
      case "$name" in [0-9][0-9]-adv-*) has_adv=1 ;; esac
    fi
  done
  [ "$count" -ge 2 ] || report "tier-a-too-few-scenarios: $skill (found $count, need >=2)"
  [ "$has_adv" -eq 1 ] || report "tier-a-no-adversarial: $skill"
}

check_tier_b() {
  local skill="$1" list="${TESTS[$1]}" p found=0
  list="${list//,/ }"
  for p in $list; do
    found=1
    [ -f "$ROOT/$p" ] || report "tier-b-missing-test: $skill -> $p"
  done
  [ "$found" -eq 1 ] || report "tier-b-missing-test: $skill (row names no test file)"
}

check_tier_c() {
  local skill="$1"
  [ -n "${REASON[$1]}" ] || report "tier-c-empty-reason: $skill"
}

# Enumerate skill dirs with the spec's [!_]* glob (excludes _shared) and check
# each against its row.
for d in "$SKILLS_DIR"/[!_]*/; do
  skill="$(basename "$d")"
  if [ -z "${TIER[$skill]+set}" ]; then
    report "no-coverage-row: $skill"
    continue
  fi
  case "${TIER[$skill]}" in
    A) check_tier_a "$skill" ;;
    B) check_tier_b "$skill" ;;
    C) check_tier_c "$skill" ;;
  esac
done

if [ "$violations" -ne 0 ]; then
  echo "lint-eval-coverage: FAIL — $violations violation(s)"
  exit 1
fi
echo "lint-eval-coverage: OK — every [!_]* skill has a conforming coverage row"
exit 0
