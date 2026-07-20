#!/usr/bin/env bash
# Self-test for evals/lint-eval-coverage.sh.
#
# Builds throwaway coverage trees under mktemp -d and drives the lint via its
# LINT_ROOT override (never touching the real repo tree), asserting: a
# conforming tree exits 0, and one fixture per R2 violation class exits
# non-zero with that violation named in the output. Same self-test pattern as
# evals/runner-selftest.sh. Ref: specs/eval-coverage-tiers/SPEC.md R3.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINT="$ROOT/evals/lint-eval-coverage.sh"

TMPS=()
cleanup() { if [ "${#TMPS[@]}" -gt 0 ]; then rm -rf "${TMPS[@]}"; fi; }
trap cleanup EXIT
# Sets $T to a fresh tmp tree and registers it for cleanup. Not called via
# command substitution — the append must land in the parent shell's TMPS.
newtree() { T="$(mktemp -d)"; TMPS+=("$T"); }

fail() {
  echo "SELFTEST FAIL: $1" >&2
  [ -n "${2:-}" ] && printf '%s\n' "$2" >&2
  exit 1
}

# --- fixture builders -------------------------------------------------------
make_skill()    { mkdir -p "$1/.claude/skills/$2"; }        # <root> <skill>
make_scenario() {                                           # <root> <skill> <name>
  local d="$1/evals/$2/$3"
  mkdir -p "$d"
  echo 'exit 0'          > "$d/setup.sh"
  echo 'a prompt'        > "$d/prompt.txt"
  echo 'exit 0'          > "$d/assert.sh"
}
make_scenario_incomplete() {                               # omits assert.sh
  local d="$1/evals/$2/$3"
  mkdir -p "$d"
  echo 'exit 0'   > "$d/setup.sh"
  echo 'a prompt' > "$d/prompt.txt"
}
write_coverage() {                                         # <root>; rows on stdin
  mkdir -p "$1/evals"
  {
    echo '# fixture coverage (lint-eval-coverage.sh)'
    echo
    echo '| Skill | Tier | Bar / reason | Tier B tests |'
    echo '|-------|------|--------------|--------------|'
    cat
  } > "$1/evals/COVERAGE.md"
}
run_lint() {                                               # <root> -> sets RC, OUT
  RC=0
  OUT="$(LINT_ROOT="$1" bash "$LINT" 2>&1)" || RC=$?
}

# A conforming three-skill tree: one row per skill, Tier A with 2 scenarios
# (one adversarial), Tier B naming an existing test file, Tier C with a reason.
build_conforming() {
  local r="$1"
  make_skill "$r" aa
  make_skill "$r" bb
  make_skill "$r" cc
  make_scenario "$r" aa 01-basic
  make_scenario "$r" aa 02-adv-refuse
  echo 'exit 0' > "$r/bb-test.sh"
  write_coverage "$r" <<'ROWS'
| aa | A | >=2 scenarios, >=1 adversarial (NN-adv-*) | |
| bb | B | deterministic core; model-free test | bb-test.sh |
| cc | C | waived: not hermetically evalable | |
ROWS
}

# --- case 0: conforming tree exits 0 ---------------------------------------
newtree; build_conforming "$T"
run_lint "$T"
[ "$RC" -eq 0 ] || fail "conforming tree should exit 0 (got $RC)" "$OUT"

# --- case 1: skill dir with no COVERAGE.md row -----------------------------
newtree; build_conforming "$T"; make_skill "$T" dd
run_lint "$T"
[ "$RC" -ne 0 ] || fail "missing-row should exit non-zero" "$OUT"
printf '%s\n' "$OUT" | grep -q 'no-coverage-row: dd' \
  || fail "missing-row violation not named for dd" "$OUT"

# --- case 2: Tier A skill with < 2 conforming scenarios --------------------
# aa has one conforming scenario (adversarial, so only the count check trips).
newtree
make_skill "$T" aa; make_skill "$T" bb; make_skill "$T" cc
make_scenario "$T" aa 01-adv-lonely
make_scenario_incomplete "$T" aa 02-broken
echo 'exit 0' > "$T/bb-test.sh"
write_coverage "$T" <<'ROWS'
| aa | A | >=2 scenarios, >=1 adversarial (NN-adv-*) | |
| bb | B | deterministic core; model-free test | bb-test.sh |
| cc | C | waived: not hermetically evalable | |
ROWS
run_lint "$T"
[ "$RC" -ne 0 ] || fail "too-few-scenarios should exit non-zero" "$OUT"
printf '%s\n' "$OUT" | grep -q 'tier-a-too-few-scenarios: aa' \
  || fail "too-few-scenarios violation not named for aa" "$OUT"

# --- case 3: Tier A skill with 2 scenarios but none adversarial ------------
newtree
make_skill "$T" aa; make_skill "$T" bb; make_skill "$T" cc
make_scenario "$T" aa 01-basic
make_scenario "$T" aa 02-more
echo 'exit 0' > "$T/bb-test.sh"
write_coverage "$T" <<'ROWS'
| aa | A | >=2 scenarios, >=1 adversarial (NN-adv-*) | |
| bb | B | deterministic core; model-free test | bb-test.sh |
| cc | C | waived: not hermetically evalable | |
ROWS
run_lint "$T"
[ "$RC" -ne 0 ] || fail "no-adversarial should exit non-zero" "$OUT"
printf '%s\n' "$OUT" | grep -q 'tier-a-no-adversarial: aa' \
  || fail "no-adversarial violation not named for aa" "$OUT"

# --- case 4: Tier B row names a test file that does not exist ---------------
newtree; build_conforming "$T"; rm "$T/bb-test.sh"
run_lint "$T"
[ "$RC" -ne 0 ] || fail "missing-test-file should exit non-zero" "$OUT"
printf '%s\n' "$OUT" | grep -q 'tier-b-missing-test: bb' \
  || fail "missing-test-file violation not named for bb" "$OUT"

# --- case 5: Tier C row with an empty reason -------------------------------
newtree
make_skill "$T" aa; make_skill "$T" bb; make_skill "$T" cc
make_scenario "$T" aa 01-basic
make_scenario "$T" aa 02-adv-refuse
echo 'exit 0' > "$T/bb-test.sh"
write_coverage "$T" <<'ROWS'
| aa | A | >=2 scenarios, >=1 adversarial (NN-adv-*) | |
| bb | B | deterministic core; model-free test | bb-test.sh |
| cc | C |  | |
ROWS
run_lint "$T"
[ "$RC" -ne 0 ] || fail "empty-reason should exit non-zero" "$OUT"
printf '%s\n' "$OUT" | grep -q 'tier-c-empty-reason: cc' \
  || fail "empty-reason violation not named for cc" "$OUT"

echo "eval-coverage lint selftest: OK (conforming + 5 violation classes)"
